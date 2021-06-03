from sys import stderr
from collections import defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urljoin, urlsplit, urlunsplit, parse_qsl, urlencode
from oso import Oso, polar_class
from polar import Variable
from polar.exceptions import PolarRuntimeError
from polar.partial import TypeConstraint
from polar.expression import Expression
from json import loads
from glom import glom
from pprint import pprint

address = "http://localhost:8000/fhir"
upstream = "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4"

session = requests.Session()
# // TODO: MFA - Don't do this in production
session.verify = False

oo_unauthorized = b"""{
  "resourceType": "OperationOutcome",
  "id": "unauthorized",
  "issue": [
    {
      "severity": "error",
      "code": "forbidden",
      "details": {
        "text": "You are not authorized to see this resource"
      }
    }
  ]
}"""

oso = None

@polar_class
class Resource:
    def __init__(self, id):
        self.id = id
    def __repr__(self):
        return "Resource(id={})".format(self.id)

def patient_from_resource(resource):
    id = resource.get("id", None)
    consent_seach_res = session.get("{}/Consent?patient={}".format(upstream, "Patient/{}".format(id))).json()
    consents = {}
    for entry in consent_seach_res.get("entry", []):
        actor_refs = glom(entry, ("resource.provision.actor", ["reference.reference"]))
        consent_flags = glom(entry, ("resource.provision.securityLabel", ["code"]))
        for actor_ref in actor_refs:
            actor_id = actor_ref.split("/")[1]
            consents[actor_id] = consent_flags
    return Patient(id, False, False, consents)

@polar_class
class Patient(Resource):
    def __init__(self, id, isAccessFrozen, isSharingDisabled, consents):
        super().__init__(id)
        self.isAccessFrozen = isAccessFrozen
        self.isSharingDisabled = isSharingDisabled
        self.consents = consents
        
    def __repr__(self):
        return "Patient(super={},isAccessFrozen={},isSharingDisabled={},consents={})".format(\
                super().__repr__(), self.isAccessFrozen, self.isSharingDisabled, self.consents)

def practitioner_from_resource(resource):
    id = resource.get("id", None)
    roles = session.get("{}/PractitionerRole?practitioner=Practitioner/{}".format(upstream, id)).json()
    teamId = None
    for entry in roles.get("entry", []):
        # Should only be one for now
        ref = glom(entry, "resource.organization.reference")
        teamId = ref.split("/")[1]
        break
    isTeamPro = bool(teamId)
    isBtgActive = False # // TODO: MFA - pull from session
    return Practitioner(id, teamId, isTeamPro, isBtgActive)
    

@polar_class
class Practitioner(Resource):
    def __init__(self, id, teamId, isTeamPro, isBtgActive):
        super().__init__(id)
        self.teamId = teamId
        self.isTeamPro = isTeamPro
        self.isBtgActive = isBtgActive

    def __repr__(self):
        return "Practitioner(super={},teamId={},isTeamPro={})".format(super().__repr__(), self.teamId, self.isTeamPro)

def related_person_from_resource(resource):
    id = resource.get("id", None)
    return RelatedPerson(id)

@polar_class
class RelatedPerson(Resource):
    def __init__(self, id):
        super().__init__(id)
    def __repr__(self):
        return "RelatedPerson(super={})".format(super().__repr__())

@polar_class
class PatientResource(Resource):
    def __init__(self, resource):
        super().__init__(resource.get("id", None))
        self.patient = resource_to_authz(session.get("{}/{}".format(upstream, glom(resource, "patient.reference"))).json())
        self.privacyFlag = glom(resource, ("meta.security", ["code"]), default=[None])[0] # Should be exactly one privacy label!
        if "id" in resource:
            provenance = session.get("{}/Provenance?target={}".format(upstream, "{}/{}".format(resource["resourceType"], resource["id"]))).json()
            for entry in provenance.get("entry", []):
                refs = glom(entry, ("resource.agent", ["who.reference"])) # Should filter for 'author' relation here.
                self.sourceIds = [ref.split("/")[1] for ref in refs]
    def __repr__(self):
        return "PatientResource(super={},privacyFlag={},patient={})".format(super().__repr__(), self.privacyFlag, self.patient)

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
        return patient_from_resource(resource)
    elif rtype == "Practitioner":
        return practitioner_from_resource(resource)
    elif rtype == "RelatedPerson":
        return related_person_from_resource(resource)
    else:
        return None

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
        req = parse_request("GET", url_request.path)

        # Short circuit public endpoint
        if req.op == "capabilities":
            resp = proxy_request(address, upstream, url_request)
            return_response(resp, resp.text, self)
            return
        
        actor = resource_to_authz(session.get("{}/{}".format(upstream, self.headers["X-Actor-Ref"])).json())
        
        ## Simple case: operations where the ID of the target is known upfront. Just fetch the relevant resource
        ## and do the authorization on that before proxying the request.
        if req.id:
            resource = resource_to_authz(session.get("{}/{}/{}".format(upstream, req.resource, req.id)).json())
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
        elif req.op == "create":
            length = int(self.headers['content-length'])
            resource = resource_to_authz(loads(self.rfile.read(length)))
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
        elif req.op == "search":
            # We don't know all the resources upfront, so use Oso's partial evaluation feature to apply what we _can_ 
            # upfront, and turn the remaining parts into additional query parameters to add for the upstream server
            resource = Variable("resource")
            constraint = TypeConstraint(resource, req.resource)
            subject = Variable("subject")
            sourceIds = Variable("sourceIds")
            
            ## Add any other constraints we can infer from the existing query parameters
            params = parse_qsl(url_request.query)
            dparams = dict(params) # // TODO: MFA - this won't fly with multiple query params with the same name
            if "patient" in dparams:
                # Resolve the actual patient
                subject = resource_to_authz(session.get("{}/{}".format(upstream, dparams["patient"])).json())
            ## // TODO: MFA - Same for sourceIds

            # Query oso, apply those rules
            results = oso.query_rule(
                "allow",
                actor,
                "read", # search and read follow the same access control rules.
                resource,
                subject, 
                sourceIds,
                bindings={resource: constraint},
                accept_expression=True,
            )

            # Turn `results` here into additional query parameters to restrict our results
            # to just the ones we're allowed to see.
            additional_params = results_to_params(results)
            
            params.extend(additional_params)
            new_url = url_request._replace(query=urlencode(params))
            resp = proxy_request(address, upstream, new_url)
            
            # If there were Expressions that we couldn't transform, then our search might contain 
            # results we aren't supposed to see. Fallback here to just authorizing all the objects in the list
            # and filter them out if we aren't supposed to see them?
            # resp = filter(resp)
            return_response(resp, resp.text, self)
        else: 
            self.send_response(400, "Unsupported operation {}".format(req.op))
            self.end_headers()

class UnhandledExpression(Exception):
    pass

def expression_to_params(expr: Expression):
    # Stupidly simplified expression to query parameters. Really this should handle everything explicitly and
    # throw if we encountered something we didn't expect.
    if expr.operator == "Isa":
        # Skip these, we already know the types we're looking at
        return []
    elif expr.operator == "In" and expr.args[1].__repr__() == "Expression(Dot, [Variable('_this'), 'sourceIds'])":
        sourceId = expr.args[0]
        return [("_security", "http://fhir.patientsknowbest.com/codesystem/source-id|{}".format(sourceId))]
    elif expr.operator == "Unify" and expr.args[1].__repr__() == "Expression(Dot, [Variable('_this'), 'privacyFlag'])":
        privacyFlag = expr.args[0]
        return [("_security", "http://fhir.patientsknowbest.com/codesystem/privacy-label|{}".format(privacyFlag))]
    else:
        return []

def results_to_params(results):
    """
    This is a really noddy function for transforming Polar Expressions into query parameters for upstream FHIR server.
    Really it should take into account the existing search params, and if those are already a subset of the ones we're 
    allowed to search for, then don't modify the query. 
    Also we should handle multiple fields in combination properly, see documentation for composing FHIR SEARCH params: 
    https://www.hl7.org/fhir/search.html
    
    :param results: 
    :return: 
    """
    all_params = []
    for res in results:
        top_expr: Expression = glom(res, "bindings.resource")
        if top_expr.operator != "And":
            raise UnhandledExpression("Can't handle operator other than 'And' as top level expression")
        
        params = []
        for sub_expr in top_expr.args:
            params.extend(expression_to_params(sub_expr))
        if len(params) > 1:
            raise UnhandledExpression("Can't handle more than 1 set of params from a single top level expression")
        all_params.extend(params)
    # Combine the query parameters as an OR expression, that is comma separated 
    final_params = defaultdict(str)
    for (k, v) in all_params:
        val = final_params[k]
        if len(val) == 0:
            val = v
        else:
            if not v in val:
                val = val + "," + v
        final_params[k]= val
    if len(final_params) > 1:
        raise UnhandledExpression("Can't properly handle more than 1 field specified in authz query param")
    return list(final_params.items())

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
        

class ParseError(Exception):
    pass


class ParseResult:
    def __init__(self, op: str, resource: str, id: str):
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
