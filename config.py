
address = "http://localhost:8000/fhir"
upstream = "https://fhiruser:change-password@localhost:9443/fhir-server/api/v4"
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

oo_notfound = b"""{
  "resourceType": "OperationOutcome",
  "id": "notfound",
  "issue": [
    {
      "severity": "error",
      "code": "not-found",
      "details": {
        "text": "Resource not found"
      }
    }
  ]
}"""
