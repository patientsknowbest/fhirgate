from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from oso import Oso
from polar import Variable
from polar.partial import TypeConstraint
from json import loads

from authz_types import resource_to_authz
from expression_to_params import results_to_params
from request_parse import parse_request
from config import upstream, address, oo_unauthorized, oo_notfound

session = requests.Session()
session.verify = False
oso = None


def osoallow(oso, *args):
    try:
        next(oso.query_rule("allow", *args))
        return True
    except StopIteration:
        return False


class FHIRGateHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")

    def do_PUT(self):
        self._handle("PUT")

    def do_PATCH(self):
        self._handle("PATCH")

    def do_DELETE(self):
        self._handle("DELETE")

    def _handle(self, method):
        url_request = urlsplit(self.path)

        # Parse out the operation, see http://hl7.org/fhir/http.html
        req = parse_request(method, url_request.path)

        # Short circuit public endpoint
        if req.op == "capabilities":
            resp = proxy_request(address, upstream, url_request)
            return_response(resp, resp.text, self)
            return

        # // TODO: MFA - Pull this from keycloak 
        actor = resource_to_authz(session, session.get("{}/{}".format(upstream, self.headers["X-Actor-Ref"])).json())

        ## Simple case: operations where the ID of the target is known upfront. Just fetch the relevant resource
        ## and do the authorization on that before proxying the request.
        if req.id:
            resource = resource_to_authz(session, session.get("{}/{}/{}".format(upstream, req.resource, req.id)).json())
            if not resource:
                self.send_response(404, "Not found")
                self.end_headers()
                self.wfile.write(oo_notfound)
            print("about to authorize")
            print("ACTOR  {}".format(actor))
            print("ACTION {}".format(req.op))
            print("TARGET {}".format(resource))
            if osoallow(oso, actor, req.op, resource, resource.patient, resource.sourceIds):
                resp = proxy_request(address, upstream, url_request)
                return_response(resp, resp.text, self)
            else:
                self.send_response(401, "Permission denied")
                self.end_headers()
                self.wfile.write(oo_unauthorized)
        ## In the create case, we have already been given the resource in the request body. Authorize _that_.
        elif req.op == "create":
            length = int(self.headers['content-length'])
            resource = resource_to_authz(session, loads(self.rfile.read(length)))
            print("about to authorize")
            print("ACTOR  {}".format(actor))
            print("ACTION {}".format(req.op))
            print("TARGET {}".format(resource))
            if osoallow(oso, actor, req.op, resource, resource.patient, resource.sourceIds):
                resp = proxy_request(address, upstream, url_request)
                return_response(resp, resp.text, self)
            else:
                self.send_response(401, "Permission denied")
                self.end_headers()
                self.wfile.write(oo_unauthorized)
        ## In the search case, be clever
        elif req.op == "search":
            ## Assign unbound variables for things we don't know upfront
            resource = Variable("resource")
            subject = Variable("subject")
            sourceIds = Variable("sourceIds")

            ## Use type constraint to narrow the search to the right kind of allow policies
            constraint = TypeConstraint(resource, req.resource)
            
            ## Get concrete values when we can infer them from the query parameters
            params = parse_qsl(url_request.query)
            dparams = dict(params)
            if "patient" in dparams:
                subject = resource_to_authz(session, session.get("{}/{}".format(upstream, dparams["patient"])).json())
            ## // TODO: MFA - Same for sourceIds?

            results = oso.query_rule(
                "allow",
                actor,
                "read",  # search and read follow the same access control rules.
                resource,
                subject,
                sourceIds,
                bindings={resource: constraint},
                accept_expression=True,
            )
            lresults = [res for res in results]
            if len(lresults) > 0:
                # Turn the evaluation results to additional query params before proxying the request
                extra_params = results_to_params(lresults)
                print("Extending search parameters with ", extra_params)
                params.extend(extra_params)
                new_url = url_request._replace(query=urlencode(params))
                resp = proxy_request(address, upstream, new_url)
                # if any results couldn't be transformed to query parameters, this is where we could post-filter the 
                # result (although it could be inefficient for large results, and would interfere with paging)
                return_response(resp, resp.text, self)
            else:
                # No results indicates authorization failure based solely on upfront information 
                self.send_response(401, "Permission denied")
                self.end_headers()
                self.wfile.write(oo_unauthorized)
        else:
            self.send_response(400, "Unsupported operation {}".format(req.op))
            self.end_headers()


def return_response(resp, body, handler):
    handler.send_response(resp.status_code)
    for k in resp.headers:
        v = resp.headers[k]
        if k != "Transfer-Encoding":
            handler.send_header(k, v)
    handler.end_headers()
    handler.wfile.write(bytes(body, 'UTF-8'))


def proxy_request(ownaddress, upstream, url_request):
    url_self = urlsplit(ownaddress)
    url_upstream = urlsplit(upstream)
    url_new = url_request._replace(scheme=url_upstream.scheme)
    url_new = url_new._replace(netloc=url_upstream.netloc)
    new_path = url_request.path.replace(url_self.path, url_upstream.path, 1)
    url_new = url_new._replace(path=new_path)
    return session.get(urlunsplit(url_new))


def run(server_class=HTTPServer, handler_class=FHIRGateHandler):
    global oso
    oso = Oso()
    oso.load_file("authorization.polar")
    url = urlsplit(address)
    server_address = (url.hostname, url.port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


if __name__ == "__main__":
    run()
