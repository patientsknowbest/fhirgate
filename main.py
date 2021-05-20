from http.server import HTTPServer, BaseHTTPRequestHandler
from oso import Oso
from requests import get
from urllib.parse import urljoin, urlsplit, urlunsplit
from fhirclient.client import FHIRClient, FHIRNotFoundException
from fhirclient.models.person import Person 

address = "http://localhost:8000/fhir"
upstream = "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4"

fhir_client = FHIRClient(settings={
    'app_id': 'upstream',
    'api_base': upstream
})
fhir_client.server.session.verify = False

class FHIRGateHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # // TODO: MFA - Parse out the request information about the actor, 
        # This should typically come from keycloak rather than a hard-coded ID.
        person_id = "1798bb3bd74-7487676b-4117-4c13-b255-ec4aba23abaf"
        actor_person = None
        if person_id:
            try:
                # // TODO: MFA - Use 
                actor_person = Person.read(person_id, fhir_client.server)
            except FHIRNotFoundException as e:
                pass
        
        # // TODO: MFA - 
        # Parse out the operation
        # For read operations, defer the authorization 'til after we got the data.
        # For search operations, parse out the search terms and authorize what we can upfront
        # and add any additional mandatory query params.
        
        url_self = urlsplit(address)
        url_upstream = urlsplit(upstream)
        url_request = urlsplit(self.path)
        url_request = url_request._replace(scheme=url_upstream.scheme)
        url_request = url_request._replace(netloc=url_upstream.netloc)
        new_path = url_request.path.replace(url_self.path, url_upstream.path, 1)
        url_request = url_request._replace(path=new_path)
        
        # Forward the request
        resp = get(urlunsplit(url_request), verify=False)
        
        # And push it back to the client
        self.send_response(resp.status_code)
        for k in resp.headers:
            v = resp.headers[k]
            if k != "Transfer-Encoding":
                self.send_header(k, v)
        self.end_headers()
        resp_body = resp.text
        
        # // TODO: MFA - post-processing
        
        self.wfile.write(bytes(resp_body, 'UTF-8'))

def run(server_class=HTTPServer, handler_class=FHIRGateHandler):
    oso = Oso()
    # oso.register_class()
    oso.load_file("authorization.polar")
    
    server_address = ('', 8000)
    
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()    
    
if __name__=="__main__":
    run()
