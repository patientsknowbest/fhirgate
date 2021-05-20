from http.server import HTTPServer, BaseHTTPRequestHandler
from oso import Oso
from polar.expression import Expression

class FHIRGateHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Fetch the authorization data & parse out the query parameters
        # Authorise with oso
        # oso.query_rule("allow", actor, action, resource, bindings=)
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"hi")

def run(server_class=HTTPServer, handler_class=FHIRGateHandler):
    oso = Oso()
    # oso.register_class()
    oso.load_file("authorization.polar")
    
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()    
    
if __name__=="__main__":
    run()
