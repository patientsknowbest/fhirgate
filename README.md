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
docker run -d -p 9443:9443 -e BOOTSTRAP_DB=true ibmcom/ibm-fhir-server
```

Activate the virtual environment and get dependencies installed
```
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

Preload sample data:
```
python load.py
```

Run the fhirgate server:
```
python main.py&
```

Run the 'integration test' script.
```
python main_it.py
```

