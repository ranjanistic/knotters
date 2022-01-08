from main.mailers import sendActionEmail, sendAlertEmail
from main.env import PUBNAME
from .models import Project, FreeProject, ProjectTransferInvitation


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
        conclusion=f"This email was generated because we have received a project submission from your Knotters account. If this wasn't you, then please report to us."
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
            'url': project.getModLink()
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

