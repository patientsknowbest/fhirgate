from unittest import TestCase, main
from main import parse_request, ParseError, ParseResult, Patient, expression_to_params, results_to_params
from polar import Variable
from polar.expression import Expression, Pattern

class TestOsoResultToParams(TestCase):
    def test_isa_ignored(self):
        p1 = expression_to_params(Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]))
        self.assertEqual([], p1)
    def test_unify_ignored(self):
        p2 = expression_to_params(Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]))
        self.assertEqual([], p2)
    def test_sourceid_to_param(self):
        p3 = expression_to_params(Expression("In", ['b60de836-3dfd-4172-90fd-bc1efb4b0adb', Expression("Dot", [Variable('_this'), 'sourceIds'])]))
        self.assertEqual([("_security", "http://fhir.patientsknowbest.com/codesystem/source-id|b60de836-3dfd-4172-90fd-bc1efb4b0adb")], p3)
    def test_privflag_to_param(self):           
        p4 = expression_to_params(Expression("Unify", ['SEXUAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])]))
        self.assertEqual([("_security", "http://fhir.patientsknowbest.com/codesystem/privacy-label|SEXUAL_HEALTH")], p4)
        
    def test_to_params1(self):        
        results = [
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("In", ['b60de836-3dfd-4172-90fd-bc1efb4b0adb', Expression("Dot", [Variable('_this'), 'sourceIds'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("In", ['11b7a2ba-17a4-4cec-a6f7-c664ba560915', Expression("Dot", [Variable('_this'), 'sourceIds'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['GENERAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['MENTAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SEXUAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SOCIAL_CARE', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['GENERAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['MENTAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SEXUAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SOCIAL_CARE', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("In", ['b60de836-3dfd-4172-90fd-bc1efb4b0adb', Expression("Dot", [Variable('_this'), 'sourceIds'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("In", ['11b7a2ba-17a4-4cec-a6f7-c664ba560915', Expression("Dot", [Variable('_this'), 'sourceIds'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['GENERAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['MENTAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SEXUAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SOCIAL_CARE', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['GENERAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['MENTAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SEXUAL_HEALTH', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}},
         {"bindings": {"resource": Expression("And", [Expression("Isa", [Variable('_this'), Pattern("Immunization", {})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'patient']), Patient("8c455d7a-fe6b-4e4f-9144-66fbc945b5de",False,False,{'11b7a2ba-17a4-4cec-a6f7-c664ba560915': ['GENERAL_HEALTH', 'MENTAL_HEALTH', 'SEXUAL_HEALTH', 'SOCIAL_CARE']})]), Expression("Unify", [Expression("Dot", [Variable('_this'), 'sourceIds']), Variable('sourceIds')]), Expression("Isa", [Variable('_this'), Pattern("PatientResource", {})]), Expression("Unify", ['SOCIAL_CARE', Expression("Dot", [Variable('_this'), 'privacyFlag'])])])}}
        ]
        params = results_to_params(results)
        self.assertEqual([("_security", "http://fhir.patientsknowbest.com/codesystem/source-id|b60de836-3dfd-4172-90fd-bc1efb4b0adb," 
                                      + "http://fhir.patientsknowbest.com/codesystem/source-id|11b7a2ba-17a4-4cec-a6f7-c664ba560915,"
                                      + "http://fhir.patientsknowbest.com/codesystem/privacy-label|GENERAL_HEALTH,"
                                      + "http://fhir.patientsknowbest.com/codesystem/privacy-label|MENTAL_HEALTH,"
                                      + "http://fhir.patientsknowbest.com/codesystem/privacy-label|SEXUAL_HEALTH,"
                                      + "http://fhir.patientsknowbest.com/codesystem/privacy-label|SOCIAL_CARE")], params)

class TestOperationTypeParser(TestCase):
    base = "http://localhost:8080/fhir"
    def test_custom(self):
        req = parse_request("POST", "/fhir/Patient/$bar", self.base)
        self.assertEqual(req, ParseResult("bar", "Patient", None))
    def test_metadata(self):
        req = parse_request("GET", "/fhir/metadata", self.base)
        self.assertEqual(req, ParseResult("capabilities", None, None))
    def test_read(self):
        req = parse_request("GET", "/fhir/Patient/123/", self.base)
        self.assertEqual(req, ParseResult("read", "Patient", "123"))
    def test_history(self):
        req = parse_request("GET", "/fhir/Patient/123/_history/4",self.base)
        self.assertEqual(req, ParseResult("vread", "Patient", "123"))
    def test_search_get(self):
        req = parse_request("GET", "/fhir/Patient/", self.base)
        self.assertEqual(req, ParseResult("search", "Patient", None))
    def test_search_post(self):
        req = parse_request("POST", "/fhir/Patient/_search", self.base)
        self.assertEqual(req, ParseResult("search", "Patient", None))
    def test_delete(self):
        req = parse_request("DELETE", "/fhir/Patient/123", self.base)
        self.assertEqual(req, ParseResult("delete", "Patient", "123"))
    def test_patch(self):
        req = parse_request("PATCH", "/fhir/Patient/123", self.base)
        self.assertEqual(req, ParseResult("patch", "Patient", "123"))
    def test_unknown(self):
        with self.assertRaises(ParseError):
            parse_request("FOO", "/fhir", self.base)

if __name__=="__main__":
    main()
