from requests import get

ABE     = "Patient/666a2a30-a142-4929-ac88-27243e602c01" # Sharing disabled
CAROL   = "Patient/8c455d7a-fe6b-4e4f-9144-66fbc945b5de"
DANIEL  = "Patient/1401dfb4-7740-4051-a534-7ff2d25ced75"
ZENU    = "Patient/9cd3b4b3-3fb1-4ef7-b16d-a2a2fad57667" # Access frozen

SUE     = "Practitioner/b60de836-3dfd-4172-90fd-bc1efb4b0adb"

if __name__=="__main__":
    # Self-access is allowed
    print(get("http://localhost:8000/fhir/Immunization/8b24c826-bd6b-11eb-ac21-8387a23fcaa5", headers={"X-Actor-Ref": CAROL}).json())
    
    # Accessing unrelated person is not
    print(get("http://localhost:8000/fhir/Immunization/8b24c826-bd6b-11eb-ac21-8387a23fcaa5", headers={"X-Actor-Ref": ABE}).json())
    
    # Accessing data where we are the source, 
    print(get("http://localhost:8000/fhir/Immunization/8b24c826-bd6b-11eb-ac21-8387a23fcaa5", headers={"X-Actor-Ref": SUE}).json())
