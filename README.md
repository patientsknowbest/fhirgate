# fhirgate

A gateway for adding efficient Attribute Based Access Control in front of any FHIR compliant server.

## architecture

fhirgate acts as a Policy Decision Point & Policy Enforcement Point in front of a FHIR API server (also known as an API gateway). The FHIR API server itself is used as the Policy Information Point.

authorization rules are implemented using [oso](osohq.com) which allows utilizing the same policy for read and search operations. Read operations are authorized post-fetch by inspecting the returned resource. Search operations have mandatory additional query parameters applied before the request is forwarded to the target FHIR server.

Prerequisites:
- python
- python-pip
- python-virtualenv
- a FHIR server

Optional: 
- httpie (for command line interaction with APIs)

For a quick FHIR server setup, run the IBM FHIR Server docker image:
```
docker run -p 9443:9443 -e BOOTSTRAP_DB=true ibmcom/ibm-fhir-server
```

Then preload it with sample data:
```
http --verify no --auth 'fhiruser:change-password' POST https://localhost:9443/fhir-server/api/v4/ < data/batch.json
```

Install and run:
```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
python main.py
```

Run the 'integration test' script which shows some sample authz successes and failures.
```
python main_it.py
```

TODO:
- FHIR client
- fetching data and mapping to flat types for authz
- forwarding read requests and post-filtering
- forwarding search requests and adding query params
- keycloak integration
