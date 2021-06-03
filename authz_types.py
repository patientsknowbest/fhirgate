from glom import glom
from polar import polar_class

from config import upstream

"""
Flattened equivalents of FHIR types for authorization purposes.
Makes writing policies simpler.
"""

@polar_class
class Resource:
    def __init__(self, id):
        self.id = id
    def __repr__(self):
        return "Resource(id={})".format(self.id)


def patient_from_resource(session, resource):
    id = resource.get("id", None)
    consent_seach_res = session.get("{}/Consent?patient={}".format(upstream, "Patient/{}".format(id))).json()
    consents = {}
    for entry in consent_seach_res.get("entry", []):
        actor_refs = glom(entry, ("resource.provision.actor", ["reference.reference"]))
        consent_flags = glom(entry, ("resource.provision.securityLabel", ["code"]))
        for actor_ref in actor_refs:
            actor_id = actor_ref.split("/")[1]
            consents[actor_id] = consent_flags
    return Patient(id, False, False, consents)


@polar_class
class Patient(Resource):
    def __init__(self, id, isAccessFrozen, isSharingDisabled, consents):
        super().__init__(id)
        self.isAccessFrozen = isAccessFrozen
        self.isSharingDisabled = isSharingDisabled
        self.consents = consents
        
    def __repr__(self):
        return "Patient(super={},isAccessFrozen={},isSharingDisabled={},consents={})".format(\
                super().__repr__(), self.isAccessFrozen, self.isSharingDisabled, self.consents)


def practitioner_from_resource(session, resource):
    id = resource.get("id", None)
    roles = session.get("{}/PractitionerRole?practitioner=Practitioner/{}".format(upstream, id)).json()
    teamId = None
    for entry in roles.get("entry", []):
        # Should only be one for now
        ref = glom(entry, "resource.organization.reference")
        teamId = ref.split("/")[1]
        break
    isTeamPro = bool(teamId)
    isBtgActive = False # // TODO: MFA - pull from session
    return Practitioner(id, teamId, isTeamPro, isBtgActive)


@polar_class
class Practitioner(Resource):
    def __init__(self, id, teamId, isTeamPro, isBtgActive):
        super().__init__(id)
        self.teamId = teamId
        self.isTeamPro = isTeamPro
        self.isBtgActive = isBtgActive

    def __repr__(self):
        return "Practitioner(super={},teamId={},isTeamPro={})".format(super().__repr__(), self.teamId, self.isTeamPro)


def related_person_from_resource(resource):
    id = resource.get("id", None)
    return RelatedPerson(id)


@polar_class
class RelatedPerson(Resource):
    def __init__(self, id):
        super().__init__(id)
    def __repr__(self):
        return "RelatedPerson(super={})".format(super().__repr__())


@polar_class
class PatientResource(Resource):
    def __init__(self, resource):
        super().__init__(resource.get("id", None))
        self.patient = resource_to_authz(session.get("{}/{}".format(upstream, glom(resource, "patient.reference"))).json())
        self.privacyFlag = glom(resource, ("meta.security", ["code"]), default=[None])[0] # Should be exactly one privacy label!
        if "id" in resource:
            provenance = session.get("{}/Provenance?target={}".format(upstream, "{}/{}".format(resource["resourceType"], resource["id"]))).json()
            for entry in provenance.get("entry", []):
                refs = glom(entry, ("resource.agent", ["who.reference"])) # Should filter for 'author' relation here.
                self.sourceIds = [ref.split("/")[1] for ref in refs]
    def __repr__(self):
        return "PatientResource(super={},patient={},privacyFlag={},sourceIds={})".format(super().__repr__(), self.patient,self.privacyFlag, self.sourceIds)


@polar_class
class Immunization(PatientResource):
    def __init__(self, resource):
        super().__init__(resource)
    def __repr__(self):
        return "Immunization(super={})".format(super().__repr__())


def resource_to_authz(session, resource):
    rtype = resource["resourceType"]
    if rtype == "Immunization":
        return Immunization(resource)
    elif rtype == "Patient":
        return patient_from_resource(session, resource)
    elif rtype == "Practitioner":
        return practitioner_from_resource(session, resource)
    elif rtype == "RelatedPerson":
        return related_person_from_resource(resource)
    else:
        return None