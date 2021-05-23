from unittest import TestCase, main
from main import parse_request, ParseError, ParseResult

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
