from requests import get
from glom import glom
from unittest import TestCase, main

"""
Requires the fhirgate application running on localhost:8000
"""

### Orgs
ORG_AIREDALE = "Organization/11b7a2ba-17a4-4cec-a6f7-c664ba560915"
ORG_BRADFORD = "Organization/30fcc0e2-4705-4dd3-b020-d900672a286c"

### Pros
# Team professional at Airedale
PRO_SUE     = "Practitioner/b60de836-3dfd-4172-90fd-bc1efb4b0adb"

# Team professional at Airedale
PRO_BILLY   = "Practitioner/28a8017c-610d-4e82-8b7d-3b0e574982b2"

# Team professional at Bradford
PRO_TINA    = "Practitioner/387f7b1a-95d2-440e-8804-470fd50573fc"

# Individual professional
PRO_DAVE    = "Practitioner/eef0c81c-4482-4287-99ed-3b77f629c399"

### Patients
# Grants General health consent to Airedale and to Bradford
PAT_CAROL   = "Patient/8c455d7a-fe6b-4e4f-9144-66fbc945b5de"
# Has 1x flu vaccine given by Sue at Airedale with general health consent flag
PAT_CAROLS_FLU = "Immunization/8b24c826-bd6b-11eb-ac21-8387a23fcaa5"
# Has 1x hib vaccine given by Sue at Airedale with sexual health consent flag
PAT_CAROLS_HIB = "Immunization/cfaf9c9d-458a-4635-bf3d-bf258690f973"

# Sharing disabled & Grants general health consent to Airedale and Bradford
PAT_ABE     = "Patient/666a2a30-a142-4929-ac88-27243e602c01"
# Has 1x flu vaccine given by Sue at Airedale with general health consent flag
PAT_ABES_FLU = "Immunization/8f26f460-20d2-4c17-9686-3601b15ef07a"
# Has 1x hib vaccine given by Sue at Airedale with sexual health consent flag
PAT_ABES_HIB = "Immunization/efc48758-8a87-4d18-8b99-2a5980f6c10d"

# Access frozen & grants general health consent to Airedale and Bradford
PAT_ZENU = "Patient/7b513f42-3536-4852-8a38-6ccb6d0ae62d"
# Has 1x flu vaccine given by Sue at Airedale with general health consent flag
PAT_ZENUS_FLU = "Immunization/3982dde0-af75-4983-90c4-e7779493d931"
# Has 1x hib vaccine given by Sue at Airedale with sexual health consent flag
PAT_ZENUS_HIB = "Immunization/84a39ca6-abd5-4f64-b8a9-b2aae63ddcf6"

class TestPatientAccess(TestCase):
    def test_access_frozen_read(self):
        # Patient who is access frozen can't see anything
        # Zenu tries to read his own flu vacs and gets unauthorized
        res = get("http://localhost:8000/fhir/{}".format(PAT_ZENUS_FLU), headers={"X-Actor-Ref": PAT_ZENU}).json()
        self.assertDictContainsSubset({"resourceType": "OperationOutcome"}, res)
        
    def test_access_frozen_search(self):
        res = get("http://localhost:8000/fhir/Immunization?patient={}".format(PAT_ZENU), headers={"X-Actor-Ref": PAT_ZENU}).json()
        self.assertDictContainsSubset({"resourceType": "OperationOutcome"}, res)
        
    def test_self_access_read(self):
        res = get("http://localhost:8000/fhir/{}".format(PAT_CAROLS_FLU), headers={"X-Actor-Ref": PAT_CAROL}).json()
        (resourceType, id) = PAT_CAROLS_FLU.split("/")
        self.assertDictContainsSubset({"resourceType": resourceType,"id": id}, res)
        
    def test_self_access_search(self):
        res = get("http://localhost:8000/fhir/Immunization?patient={}".format(PAT_CAROL), headers={"X-Actor-Ref": PAT_CAROL}).json()
        lresourceids = glom(res, ("entry", ["resource.id"]))
        expectedids = list(map(lambda x: x.split("/")[1], [PAT_CAROLS_FLU, PAT_CAROLS_HIB]))
        self.assertListEqual(lresourceids, expectedids)
        
    def test_patient_read_other_patient(self):
        res = get("http://localhost:8000/fhir/{}".format(PAT_ABES_FLU), headers={"X-Actor-Ref": PAT_CAROL}).json()
        self.assertDictContainsSubset({"resourceType": "OperationOutcome"}, res)

    def test_patient_search_other_patient(self):
        res = get("http://localhost:8000/fhir/Immunization?patient={}".format(PAT_ZENU), headers={"X-Actor-Ref": PAT_CAROL}).json()
        self.assertDictContainsSubset({"resourceType": "OperationOutcome"}, res)


class TestTeamProAccess(TestCase):
    def test_teampro_read_access_frozen_source(self):
        res = get("http://localhost:8000/fhir/{}".format(PAT_ZENUS_FLU), headers={"X-Actor-Ref": PRO_SUE}).json()
        (resourceType, id) = PAT_ZENUS_FLU.split("/")
        self.assertDictContainsSubset({"resourceType": resourceType,"id": id}, res)
        
    def test_teampro_search_access_frozen_source(self):
        res = get("http://localhost:8000/fhir/Immunization?patient={}".format(PAT_ZENU), headers={"X-Actor-Ref": PRO_SUE}).json()
        lresourceids = glom(res, ("entry", ["resource.id"]))
        expectedids = list(map(lambda x: x.split("/")[1], [PAT_ZENUS_FLU, PAT_ZENUS_HIB]))
        self.assertListEqual(lresourceids, expectedids)

    def test_teampro_read_access_frozen_consent(self):
        res = get("http://localhost:8000/fhir/{}".format(PAT_ZENUS_FLU), headers={"X-Actor-Ref": PRO_TINA}).json()
        (resourceType, id) = PAT_ZENUS_FLU.split("/")
        self.assertDictContainsSubset({"resourceType": resourceType,"id": id}, res)
        
    def test_teampro_read_org_authored_no_consent(self):
        res = get("http://localhost:8000/fhir/{}".format(PAT_CAROLS_HIB), headers={"X-Actor-Ref": PRO_BILLY}).json()
        (resourceType, id) = PAT_CAROLS_HIB.split("/")
        self.assertDictContainsSubset({"resourceType": resourceType,"id": id}, res)
        
    def test_teampro_search_sharingdisabled(self):
        res = get("http://localhost:8000/fhir/Immunization?patient={}".format(PAT_ABE), headers={"X-Actor-Ref": PRO_TINA}).json()
        ## This one results in 0, because we can't reject it outright but we do end up searching, just find nothing
        ## because it's all filtered by the additional params.
        self.assertDictContainsSubset({"total": 0}, res)
        
    def test_teampro_read_consent(self):
        res = get("http://localhost:8000/fhir/{}".format(PAT_CAROLS_FLU), headers={"X-Actor-Ref": PRO_TINA}).json()
        (resourceType, id) = PAT_CAROLS_FLU.split("/")
        self.assertDictContainsSubset({"resourceType": resourceType,"id": id}, res)

    def test_teampro_read_noconsent(self):
        ## Tina can't read Carol's sexual health data.
        res = get("http://localhost:8000/fhir/{}".format(PAT_CAROLS_HIB), headers={"X-Actor-Ref": PRO_TINA}).json()
        self.assertDictContainsSubset({"resourceType": "OperationOutcome"}, res)

    def test_teampro_search_consent(self):
        res = get("http://localhost:8000/fhir/Immunization?patient={}".format(PAT_CAROL), headers={"X-Actor-Ref": PRO_TINA}).json()
        ## Should just see the one we have consent for (flu)
        lresourceids = glom(res, ("entry", ["resource.id"]))
        expectedids = list(map(lambda x: x.split("/")[1], [PAT_CAROLS_FLU]))
        self.assertListEqual(lresourceids, expectedids)
    
if __name__=="__main__":
    main()

# Test scenarios, need to demonstrate for search & read operations these rules are applied
# Team Practitioner can see the data if the patient has granted consent to their team

# Individual Practitioner can't see data for access frozen patients
# Individual Practitioner can see data they personally have authored (but have no consent for)
# Individual Practitioner can't see data for sharing disabled patients, even if they have consent
# Individual Practitioner can see data where they personally have consent