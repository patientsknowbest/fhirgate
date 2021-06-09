import requests
import os
from config import upstream
from glob import glob

session = requests.Session()
session.verify = False

def loadfile(filename):
    with open(filename) as f:
        res = session.post(upstream, f, headers={"Content-Type": "application/fhir+json"})
        if res.status_code not in [200, 201]:
            print(res.text)
            raise Exception("oops")    

if __name__=="__main__":
    for f in glob("data/org.*.json"):
        loadfile(f)
    for f in glob("data/pro.*.json"):
        loadfile(f)
    for f in glob("data/pat.*.json"):
        loadfile(f)