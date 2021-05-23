### Pseudo-polar for our full authorization rules using imaginary data types ###
# Typical 'Medical data' points (Immunization, MedicationStatement etc)
allow(patient: Patient, "read", immunization: Immunization) if
    access_frozen_check(patient) and
        self_check(patient, immumization);

allow(carer: RelatedPerson, "read", immunization: Immunization) if
    access_frozen_check(carer, immunization) and (  
        source_check(carer, immunization) or
        consent_check(carer, immunization));

allow(practitioner, Practitioner, "read", immunization: Immunization) if
    access_frozen_check(practitioner, immunization) and (  
        source_check(practitioner, immunization) or
        consent_check(practitioner, immunization));

# Access frozen #
access_frozen_check(patient: Patient) if 
    not patient.isAccessFrozen;

access_frozen_check(carer: RelatedPerson, resource: PatientResource) if
    not carer.isAccessFrozen and 
        not resource.patient.isAccessFrozen;

access_frozen_check(practitioner: Practitioner, resource: PatientResource) if
    practitioner.isTeamPro or
    	not resource.patient.isAccessFrozen;

# self access #
self_check(patient: Patient, resource) if
    resource.patient.id == patient.id;

# source access (AKA team data view) #
source_check(carer: RelatedPerson, resource: PatientResource) if
    resource.sourcePersonId == carer.id;

source_check(practitioner: Practitioner, resource: PatientResource) if
    resource.sourceTeamId == practitioner.teamId or
        resource.sourcePersonId == practitioner.id;

# consent access #
consent_check(carer: RelatedPerson, resource: PatientResource) if
    sharing_disabled_check(resource) and (
    	carerId = carer.id and
        resource.privacyFlag in resource.patient.consents.(carerId));

consent_check(practitioner: Practitioner, resource: PatientResource) if
    sharing_disabled_check(practitioner, resource) and
        (practitioner.isBtgActive or (
	    practitionerId = practitioner.id and
	    practitionerTeamId = practitioner.teamId and
            resource.privacyFlag in resource.patient.consents.(practitionerId)
	        or resource.privacyFlag in resource.patient.consents.(practitionerTeamId)));

sharing_disabled_check(resource: PatientResource) if
    not resource.patient.isSharingDisabled;

sharing_disabled_check(practitioner: Practitioner, resource: PatientResource) if
    practitioner.isTeamPro or
        not resource.patient.isSharingDisabled;

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

