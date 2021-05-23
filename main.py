from sys import stderr
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from requests import get
from urllib.parse import urljoin, urlsplit, urlunsplit
from oso import Oso, polar_class
from json import loads

address = "http://localhost:8000/fhir"
upstream = "http://fhiruser:change-password@localhost:8080/fhir-server/api/v4"

oso = None

class AuthzError(Exception):
    pass

@polar_class
class Resource:
    def __init__(self, resource):
        self.id = resource["id"]
    def __repr__(self):
        return "Resource(id={})".format(self.id)

@polar_class
class Patient(Resource):
    def __init__(self, resource):
        super().__init__(resource)
        self.isAccessFrozen = False
        self.isSharingDisabled = False
        consentres = get("{}/Consent?patient={}".format(upstream, "Patient/{}".format(self.id))).json()
        self.consents = {}
        for e in consentres.get("entry", []):
            aref = e["provision"]["actor"]["reference"]
            labels = e["provision"]["securityLabel"]
            self.consents[aref.split("/")[1]] = [l["code"] for l in labels]
    def __repr__(self):
        return "Patient(super={},isAccessFrozen={},isSharingDisabled={},consents={})".format(\
                super().__repr__(), self.isAccessFrozen, self.isSharingDisabled, self.consents)

@polar_class
class Practitioner(Resource):
    def __init__(self, resource):
        super().__init__(resource)
        self.isTeamPro = False

    def __repr__(self):
        return "Practitioner(super={},isTeamPro={})".format(super().__repr__(), self.isTeamPro)

@polar_class
class RelatedPerson(Resource):
    def __init__(self, resource):
        super().__init__(resource)
    def __repr__(self):
        return "RelatedPerson(super={})".format(super().__repr__())

@polar_class
class PatientResource(Resource):
    def __init__(self, resource):
        super().__init__(resource)
        patres = resource_to_authz(get("{}/{}".format(upstream, resource["patient"]["reference"])).json())
        self.patient = patres
    def __repr__(self):
        return "PatientResource(super={},patient={})".format(super().__repr__(), self.patient)

@polar_class
class Immunization(PatientResource):
    def __init__(self, resource):
        super().__init__(resource)
    def __repr__(self):
        return "Immunization(super={})".format(super().__repr__())

def resource_to_authz(resource):
    rtype = resource["resourceType"]
    if rtype == "Immunization":
        return Immunization(resource)
    elif rtype == "Patient":
        return Patient(resource)
    elif rtype == "Practitioner":
        return Practitioner(resource)
    elif rtype == "RelatedPerson":
        return RelatedPerson(resource)
    else:
        raise AuthzError("Resource type {} is not supported".format(rtype))

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

        # // TODO: MFA - Parse out the request information about the actor, 
        # This should typically come from keycloak rather than a hard-coded ID.
        # If will be one of the Person-type resources: Patient, Practitioner, or RelatedPerson
        actor_ref = "Patient/1799108bb14-b87fc3b1-068f-4f6d-8e03-8f977886e625"
        actor = resource_to_authz(get("{}/{}".format(upstream, actor_ref)).json())
        
        # Parse out the operation, see http://hl7.org/fhir/http.html
        req = parse_request("GET", url_request.path)

        if req.op == "capabilities":
            resp = proxy_request(address, upstream, url_request)
            return_response(resp, resp.text, self)
        elif req.id:
            resource = resource_to_authz(get("{}/{}/{}".format(upstream, req.resource, req.id)).json())
            print("about to authorize")
            print("ACTOR  {}".format(actor))
            print("ACTION {}".format(req.op))
            print("TARGET {}".format(resource))
            if oso.is_allowed(actor, req.op, resource):
                resp = proxy_request(address, upstream, url_request)
                return_response(resp, resp.text, self)
            else:
                self.send_response(401, "Permission denied")
                self.end_headers()
        elif req.op == "create":
            length = int(self.headers['content-length'])
            resource = resource_to_authz(loads(self.rfile.read(length)))
            print("about to authorize")
            print("ACTOR  {}".format(actor))
            print("ACTION {}".format(req.op))
            print("TARGET {}".format(resource))
            if oso.is_allowed(actor, req.op, resource):
                resp = proxy_request(address, upstream, url_request)
                return_response(resp, resp.text, self)
            else:
                self.send_response(401, "Permission denied")
                self.end_headers()
        elif req.op == "search":
            print("WARNING authz not implemented for search", file=stderr)
            # Parse out the search params and authorize the search
            # Then proxy
            # Then MAYBE double check the results
            resp = proxy_request(address, upstream, url_request)
            return_response(resp, resp.text, self)
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
    return get(urlunsplit(url_new), verify=False)
        

class ParseError(Exception):
    pass


class ParseResult:
    def __init__(self, op, resource, id):
        self.op = op
        self.resource = resource
        self.id = id
    def __repr__(self):
        return "ParseResult(op={},resource={},id={})".format(self.op, self.resource, self.id)
    def __eq__(self,other):
        if isinstance(other, ParseResult):
            return self.op == other.op \
               and self.resource == other.resource \
               and self.id == other.id
        return False


def parse_request(method = "", path = "", base = address):
    """
    determines the FHIR operation type, resource name, ID and query parameters for an HTTP request to a FHIR server
    http://hl7.org/fhir/http.html
    // TODO: MFA - replace this with the HAPI FHIR code which must already exist to do this.
    """
    # Remove the base URL from our path
    url_self = urlsplit(base)
    path = path.replace(url_self.path, "")

    named_op = None
    op = None
    resource = None
    id = None

    # Short circuit for named operations
    optoks = path.split("$")
    if len(optoks) > 2:
        raise ParseError('More than 1 named operation delimiter $')
    elif len(optoks) == 2:
        named_op = optoks[1]
        path = optoks[0]

    # Trim any leading or trailing slashes, don't care about those
    path_elems = path.strip("/").split("/")

    # Short circuit the metadata 
    if len(path_elems) >= 1 and path_elems[0] == "metadata":
        return ParseResult("capabilities", None, None)

    # Logic time
    if method == "GET":
        if len(path_elems) == 2:
            op = "read"
            resource = path_elems[0]
            id = path_elems[1]
        elif len(path_elems) == 4 and path_elems[2] == "_history":
            op = "vread"
            resource = path_elems[0]
            id = path_elems[1]
        elif len(path_elems) == 1:
            op = "search"
            resource = path_elems[0]
        else:
            raise ParseError("Unable to parse {} {}".format(method, path))
    elif method == "PUT":
        if len(path_elems) == 2:
            op = "update"
            resource = path_elems[0]
            id = path_elems[1]
        else:
            raise ParseError("Unable to parse {} {}".format(method, path))
    elif method == "POST":
        if len(path_elems) == 2  and path_elems[1] == "_search":
            op = "search"
            resource = path_elems[0]
        elif len(path_elems) == 1:
            op = "create"
            resource = path_elems[0]
    elif method == "PATCH":
        if len(path_elems) == 2:
            op = "patch"
            resource = path_elems[0]
            id = path_elems[1]
        else:
            raise ParseError("Unable to parse {} {}".format(method, path))
    elif method == "DELETE":
        if len(path_elems) == 2:
            op = "delete"
            resource = path_elems[0]
            id = path_elems[1]
        else:
            raise ParseError("Unable to parse {} {}".format(method, path))
    else:
        raise ParseError("Unable to parse {} {}".format(method, path))
    if named_op:
        op = named_op
    return ParseResult(op, resource, id)

def run(server_class=HTTPServer, handler_class=FHIRGateHandler):
    global oso
    oso = Oso()
    oso.load_file("authorization.polar")
    
    url = urlsplit(address)
    server_address = (url.hostname, url.port)
    
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()    
    

if __name__=="__main__":
    run()
