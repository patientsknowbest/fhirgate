### Pseudo-polar for our full authorization rules using imaginary data types ###
# Typical 'Medical data' points (Immunization, MedicationStatement etc)
allow(patient: Patient, "read", resource: Immunization, subject: Patient, sourceIds) if
    access_frozen_check(patient) and
        self_check(patient, subject);

allow(carer: RelatedPerson, "read", resource: Immunization, subject: Patient, sourceIds) if
    access_frozen_check(carer, subject) and (  
        source_check(carer, sourceIds) or
        consent_check(carer, resource, subject));

allow(practitioner: Practitioner, "read", resource: Immunization, subject: Patient, sourceIds) if
    access_frozen_check(practitioner, subject) and (  
        source_check(practitioner, sourceIds) or
            consent_check(practitioner, resource, subject));

# Access frozen #
access_frozen_check(patient: Patient) if 
    not patient.isAccessFrozen;

access_frozen_check(carer: RelatedPerson, subject: Patient) if
    not carer.isAccessFrozen and 
        not subject.isAccessFrozen;

access_frozen_check(practitioner: Practitioner, subject: Patient) if
    practitioner.isTeamPro or
    	not subject.isAccessFrozen;

# self access #
self_check(patient: Patient, subject: Patient) if
    subject.id == patient.id;

# source access (AKA team data view) #
source_check(carer: RelatedPerson, sourceIds) if
    carer.id in sourceIds;

source_check(practitioner: Practitioner, sourceIds) if
    practitioner.id in sourceIds or
        practitioner.teamId in sourceIds;

# consent access #
consent_check(carer: RelatedPerson, resource: PatientResource, subject: Patient) if
    sharing_disabled_check(subject) and (
    	carerId := carer.id and
        resource.privacyFlag in subject.consents.(carerId));

consent_check(practitioner: Practitioner, resource: PatientResource, subject: Patient) if
    sharing_disabled_check(practitioner, subject) and
        (practitioner.isBtgActive or (
	    practitionerId := practitioner.id and
	    practitionerTeamId := practitioner.teamId and
            resource.privacyFlag in subject.consents.(practitionerId)
	        or resource.privacyFlag in subject.consents.(practitionerTeamId)));

sharing_disabled_check(subject: Patient) if
    not subject.isSharingDisabled;

sharing_disabled_check(practitioner: Practitioner, subject: Patient) if
    practitioner.isTeamPro or
        not subject.isSharingDisabled;

# More complex Communication type
# allow(actor: Actor, operation: String, communication: Communication) if 
#     access_frozen_check(actor, communication) and 
#     private_communication_check(actor, communication) and 
#     draft_communication_check(actor, communication) and (  
#        self_check(actor, communication) or
#        source_check(actor, communication) or
#        consent_check(actor, communication) or 
#        communication_participant_check(actor, communication));
#
# private_communication_check(actor: Actor, communication: Communication) if
# # // TODO: MFA - Semantics of private conversations, can the team access?
# # what about system users? Current rules say no
#     not communication.private or 
#         communication.sender = actor 
#             or communication.recipients.contains(actor);
# 
# draft_communication_check(actor: Actor, communication: Communication) if 
#     not communication.draft or 
#         communication.sender = actor;
# 
# # // TODO: MFA - This is only necessary if it's possible to have someone as 
# # a participant when they don't have consent for the privacy flag of the 
# # conversation.
# communication_participant_check(actor: Actor, communication: Communication) if 
#     communication.participants.contains(actor);

