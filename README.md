# fhirgate

A gateway for adding efficient Attribute Based Access Control in front of any FHIR compliant server.

## architecture

fhirgate acts as a Policy Decision Point & Policy Enforcement Point in front of a FHIR API server (also known as an API gateway). The FHIR API server itself is used as the Policy Information Point.

authorization rules are implemented using [oso](osohq.com) which allows utilizing the same policy for read and search operations. Read operations are authorized post-fetch by inspecting the returned resource. Search operations have mandatory additional query parameters applied before the request is forwarded to the target FHIR server.

Prerequisites:
- python
- python-pip
- python-virtualenv

Install and run:
```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
python main.py
```

The server is listening on port 8000

TODO:
- FHIR client
- fetching data and mapping to flat types for authz
- forwarding read requests and post-filtering
- forwarding search requests and adding query params
- keycloak integration
