from main.mailers import sendActionEmail, sendAlertEmail
from main.env import PUBNAME
from .models import CoreModerationTransferInvitation, CoreProject, CoreProjectDeletionRequest, Project, FreeProject, ProjectModerationTransferInvitation, ProjectTransferInvitation, VerProjectDeletionRequest


def freeProjectCreated(project: FreeProject):
    """
    Project has been submitted for moderation
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='New Project Created!',
        header=f"Yay! You have successfully created a new project - {project.name} - on {PUBNAME}. Now it is visible to everyone at the following link.",
        actions=[{
            'text': 'View project',
            'url': project.getLink()
        }],
        footer=f"You can visit the link to get started, bring people to contribute to your project, or just start with adding more details to your project!",
        conclusion=f"This email was sent because we have received a project from your {PUBNAME} account. If this wasn't you, then please report to us."
    )

def freeProjectDeleted(project: FreeProject):
    """
    Project has been submitted for moderation
    """
    return sendAlertEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Deleted',
        header=f"This is to inform you that your project - {project.name} ({project.nickname}) - has been deleted on {PUBNAME}, with all its associated data.",
        footer=f"You can always create a new project, whenever you like to start one.",
        conclusion=f"This email was sent because a project from your {PUBNAME} account was deleted. If this wasn't you, then please report to us."
    )

def sendProjectSubmissionNotification(project: Project):
    """
    Project has been submitted for moderation
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Status: Moderation',
        header=f"This is to inform you that we have received your recently submitted project - {project.name} - for moderation. A moderator was assigned to review it.",
        actions=[{
            'text': 'View moderation state',
            'url': project.getModLink()
        }],
        footer=f"We'll notify you as soon as the moderator reviews your project submission. Till then, chill out! NOTE: We're lenient.",
        conclusion=f"This email was sent because we have received a project submission from your Knotters account. If this wasn't you, then please report to us."
    )

def coreProjectSubmissionNotification(coreproject: CoreProject):
    """
    Project has been submitted for moderation
    """
    return sendActionEmail(
        to=coreproject.creator.getEmail(),
        username=coreproject.creator.getFName(),
        subject='Project Status: Moderation',
        header=f"This is to inform you that we have received your recently submitted core project request - {coreproject.name} - for moderation. Moderator has been assigned to review it.",
        actions=[{
            'text': 'View moderation state',
            'url': coreproject.getModLink()
        }],
        footer=f"We'll notify you as soon as the moderator reviews your project submission. You can check the status anytime from above link.",
        conclusion=f"This email was sent because we have received a project submission from your Knotters account. If this wasn't you, then please report to us."
    )



def sendProjectApprovedNotification(project: Project):
    """
    Project has been approved by moderator
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Status: Approved',
        header=f"Congratulations! Your submitted project - {project.name} - has been reviewed, and has been approved by the assigned moderator. " +
        "You can get more details on this by visiting the moderation page of your project submission.",
        actions=[{
            'text': 'View moderation',
            'url': project.getModLink()
        }],
        footer=f"Your project's profile page & other related setup will be available in a few moments. Cheers! The moderator & community at {PUBNAME} will be working together with you on {project.name}.",
        conclusion=f"This email was generated because a project submission received from your {PUBNAME} account has been approved. If this is unfamiliar, then please report to us."
    )

def sendCoreProjectApprovedNotification(project: CoreProject):
    """
    Core Project has been approved by moderator
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Core Project Status: Approved',
        header=f"Congratulations! Your submitted core project - {project.name} - has been reviewed, and has been approved by the assigned moderator. " +
        "You can get more details on this by visiting the moderation page of your project submission.",
        actions=[{
            'text': 'View moderation',
            'url': project.getModLink()
        }],
        footer=f"Your project's profile page & other related setup will be available in a few moments. The moderator & community at {PUBNAME} will be working on {project.name}.",
        conclusion=f"This email was sent because a core project submission received from your {PUBNAME} account has been approved. If this is unfamiliar, then please report to us."
    )


def projectRejectedNotification(project: Project):
    """
    Project has been rejected by moderator
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Status: Rejected',
        header=f"This is to inform you that your submitted project - {project.name} - has been reviewed, and unfortunately rejected by the assigned moderator. " +
        "You can get more details on this by visiting the moderation page of your project submission.",
        actions=[{
            'text': 'View moderation',
            'url': project.getLink()
        }],
        footer=f"The moderator must have found something unacceptable, but if you think this is a mistake, then you might be able to resubmit the same project for moderation. This is unfortunate.",
        conclusion=f"This email was generated we have rejected a project submission received from your {PUBNAME} account. If this is unfamiliar, then please report to us."
    )

def projectTransferInvitation(invite:ProjectTransferInvitation):
    """
    Invitation to accept project ownership
    """
    if invite.resolved: return False
    if invite.expired: return False
    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Project Transfer Invite",
        header=f"You've been invited to accept ownership of project {invite.baseproject.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
        actions=[{
            'text': 'View Invitation',
            'url': invite.get_link
        }],
        footer=f"Visit the above link to decide whether you'd want to take control of the project.",
        conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
    )
    return sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Project Transfer Initiated",
        header=f"This is to inform you that you've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept ownership of your project {invite.baseproject.name}.",
        actions=[{
            'text': 'View projet',
            'url': invite.baseproject.get_link
        }],
        footer=f"If they decline, then your project will not get transferred to them.",
        conclusion=f"If this action is unfamiliar, then you should delete the tranfer invite by visiting your project's profile."
    )

def projectTransferAcceptedInvitation(invite:ProjectTransferInvitation):
    """
    Invitation to accept project ownership
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Project Transfer Success",
        header=f"This is to inform you that your project, {invite.baseproject.name}, has been successfully transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View projet',
            'url': invite.baseproject.get_link
        }],
        footer=f"This action was irreversible, and now they control this project and you've been detached from it.",
        conclusion=f"If this action is unfamiliar, then you may contact the new owner, or contact us."
    )

    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Project Ownership Accepted",
        header=f"This is to inform you that you've accepted the ownership of {invite.baseproject.name}.",
        actions=[{
            'text': 'View Project',
            'url': invite.baseproject.get_link
        }],
        footer=f"Now you have the control and will be shown as creator of the project at {PUBNAME}",
        conclusion=f"This email was sent because you've accepted the project's ownership."
    )

def projectTransferDeclinedInvitation(invite:ProjectTransferInvitation):
    """
    Invitation to accept project ownership
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Project Transfer Failed",
        header=f"This is to inform you that your project, {invite.baseproject.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View projet',
            'url': invite.baseproject.get_link
        }],
        footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
        conclusion=f"If this action is unfamiliar, then you may contact us."
    )

def projectModTransferInvitation(invite:ProjectModerationTransferInvitation):
    """
    Invitation to accept project moderatorship
    """
    if invite.resolved: return False
    if invite.expired: return False
    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Verified Project Moderation Transfer Invite",
        header=f"You've been invited to accept moderatorship of verified project {invite.project.name} by its current moderator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
        actions=[{
            'text': 'View Invitation',
            'url': invite.get_link
        }],
        footer=f"Visit the above link to decide whether you'd want to take moderatorship of the verified project.",
        conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
    )
    return sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Verified Project Moderation Transfer Initiated",
        header=f"This is to inform you that you've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept moderatorship of the verified project {invite.project.name}.",
        actions=[{
            'text': 'View Verified Project',
            'url': invite.project.get_link
        }],
        footer=f"If they decline, then your moderatorship of this verified project will not get transferred to them.",
        conclusion=f"If this action is unfamiliar, then you should delete the tranfer invite by visiting this verified project's profile."
    )

def projectModTransferAcceptedInvitation(invite:ProjectModerationTransferInvitation):
    """
    Invitation to accept project moderatorship
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Verified Project Moderation Transfer Success",
        header=f"This is to inform you that your moderatorship of the verified project, {invite.project.name}, has been successfully transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View Verified Project',
            'url': invite.project.get_link
        }],
        footer=f"This action was irreversible, and now they control this verified project as moderator and you've been detached from it.",
        conclusion=f"If this action is unfamiliar, then you may contact the new moderator, or contact us."
    )

    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Verified Project Moderation Accepted",
        header=f"This is to inform you that you've accepted the moderatorship of {invite.project.name}.",
        actions=[{
            'text': 'View Verified Project',
            'url': invite.project.get_link
        }],
        footer=f"Now you have the control and will be shown as moderator of the verified project at {PUBNAME}",
        conclusion=f"This email was sent because you've accepted the verified project's moderatorship."
    )

def projectModTransferDeclinedInvitation(invite:ProjectModerationTransferInvitation):
    """
    Invitation to accept project moderatorship
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Verified Project Moderation Transfer Failed",
        header=f"This is to inform you that your moderatorship of the verified project, {invite.project.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View Verified Project',
            'url': invite.project.get_link
        }],
        footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
        conclusion=f"If this action is unfamiliar, then you may contact us."
    )

def coreProjectModTransferInvitation(invite:CoreModerationTransferInvitation):
    """
    Invitation to accept project moderatorship
    """
    if invite.resolved: return False
    if invite.expired: return False
    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Core Project Moderation Transfer Invite",
        header=f"You've been invited to accept moderatorship of core project {invite.coreproject.name} by its current moderator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
        actions=[{
            'text': 'View Invitation',
            'url': invite.get_link
        }],
        footer=f"Visit the above link to decide whether you'd want to take moderatorship of the coreproject.",
        conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
    )
    return sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Core Project Moderation Transfer Initiated",
        header=f"This is to inform you that you've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept moderatorship of the core project {invite.coreproject.name}.",
        actions=[{
            'text': 'View Core Project',
            'url': invite.coreproject.get_link
        }],
        footer=f"If they decline, then your moderatorship of this core project will not get transferred to them.",
        conclusion=f"If this action is unfamiliar, then you should delete the tranfer invite by visiting this core project's profile."
    )

def coreProjectModTransferAcceptedInvitation(invite:CoreModerationTransferInvitation):
    """
    Invitation to accept project moderatorship
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Core Project Moderation Transfer Success",
        header=f"This is to inform you that your moderatorship of the core project, {invite.coreproject.name}, has been successfully transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View Core Project',
            'url': invite.coreproject.get_link
        }],
        footer=f"This action was irreversible, and now they control this core project as moderator and you've been detached from it.",
        conclusion=f"If this action is unfamiliar, then you may contact the new moderator, or contact us."
    )

    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Core Project Moderation Accepted",
        header=f"This is to inform you that you've accepted the moderatorship of {invite.coreproject.name}.",
        actions=[{
            'text': 'View Core Project',
            'url': invite.coreproject.get_link
        }],
        footer=f"Now you have the control and will be shown as moderator of the core project at {PUBNAME}",
        conclusion=f"This email was sent because you've accepted the core project's moderatorship."
    )

def coreProjectModTransferDeclinedInvitation(invite:CoreModerationTransferInvitation):
    """
    Invitation to accept project moderatorship
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Core Project Moderation Transfer Failed",
        header=f"This is to inform you that your moderatorship of the core project, {invite.coreproject.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View Core Project',
            'url': invite.coreproject.get_link
        }],
        footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
        conclusion=f"If this action is unfamiliar, then you may contact us."
    )


def verProjectDeletionRequest(invite:VerProjectDeletionRequest):
    """
    Request to delete a verified project
    """
    if invite.resolved: return False
    if invite.expired: return False
    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Verified Project Deletion Request",
        header=f"You've been requested to delete the verified project {invite.project.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
        actions=[{
            'text': 'View Request',
            'url': invite.get_link
        }],
        footer=f"Visit the above link to decide whether you'd accept or decline to do so.",
        conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
    )
    return sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Verified Project Deletion Requested",
        header=f"This is to inform you that you've requested {invite.receiver.getName()} ({invite.receiver.getEmail()}) to delete the verified project {invite.project.name}.",
        actions=[{
            'text': 'View Verified Project',
            'url': invite.project.get_link
        }],
        footer=f"If they decline, then the project will not get deleted, else, deletion will start permanently.",
        conclusion=f"If this action is unfamiliar, then you should cancel the request by visiting this verified project on {PUBNAME}, as soon as possible."
    )

def verProjectDeletionAcceptedRequest(invite:VerProjectDeletionRequest):
    """
    Accepted request to verified project deletion
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Verified Project Deletion Accepted",
        header=f"This is to inform you that your request to delete the verified project, {invite.project.name}, has been accepted by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        footer=f"This action was irreversible, and the project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon.",
        conclusion=f"This email was sent because you had requested deletion of a verified project."
    )

    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Verified Project Deletion Accepted",
        header=f"This is to inform you that you've accepted to delete the verified project {invite.project.name}.",
        footer=f"The project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon. This action was irreversible, as you should know already.",
        conclusion=f"This email was sent because you've deleted a verified project."
    )

def verProjectDeletionDeclinedRequest(invite:VerProjectDeletionRequest):
    """
    Declinded request to verified project deletion
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Verified Project Deletion Failed",
        header=f"This is to inform you that your deletion of the verified project, {invite.project.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View Verified Project',
            'url': invite.project.get_link
        }],
        footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
        conclusion=f"If this action is unfamiliar, then you may contact us."
    )

def coreProjectDeletionRequest(invite:CoreProjectDeletionRequest):
    """
    Request to delete a core project
    """
    if invite.resolved: return False
    if invite.expired: return False
    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Core Project Deletion Request",
        header=f"You've been requested to delete the core project {invite.coreproject.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
        actions=[{
            'text': 'View Request',
            'url': invite.get_link
        }],
        footer=f"Visit the above link to decide whether you'd accept or decline to do so.",
        conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
    )
    return sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Core Project Deletion Requested",
        header=f"This is to inform you that you've requested {invite.receiver.getName()} ({invite.receiver.getEmail()}) to delete the core project {invite.coreproject.name}.",
        actions=[{
            'text': 'View Core Project',
            'url': invite.coreproject.get_link
        }],
        footer=f"If they decline, then the project will not get deleted, else, deletion will start permanently.",
        conclusion=f"If this action is unfamiliar, then you should cancel the request by visiting this core project on {PUBNAME}, as soon as possible."
    )

def coreProjectDeletionAcceptedRequest(invite:CoreProjectDeletionRequest):
    """
    Accepted Request to core project deletion
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Core Project Deletion Accepted",
        header=f"This is to inform you that your request to delete the core project, {invite.coreproject.name}, has been accepted by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        footer=f"This action was irreversible, and the project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon.",
        conclusion=f"This email was sent because you had requested deletion of a core project."
    )

    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Core Project Deletion Accepted",
        header=f"This is to inform you that you've accepted to delete the core project {invite.coreproject.name}.",
        footer=f"The project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon. This action was irreversible, as you should know already.",
        conclusion=f"This email was sent because you've deleted a core project."
    )

def coreProjectDeletionDeclinedRequest(invite:CoreProjectDeletionRequest):
    """
    Declined Request to core project deletion
    """
    if not invite.resolved: return False
    sendActionEmail(
        to=invite.sender.getEmail(),
        username=invite.sender.getFName(),
        subject=f"Core Project Deletion Failed",
        header=f"This is to inform you that your moderatorship of the core project, {invite.coreproject.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
        actions=[{
            'text': 'View Core Project',
            'url': invite.coreproject.get_link
        }],
        footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
        conclusion=f"If this action is unfamiliar, then you may contact us."
    )

