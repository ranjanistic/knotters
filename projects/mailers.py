from main.mailers import sendActionEmail
from .models import Project


def sendProjectSubmissionNotification(project: Project):
    """
    Project has been submitted for moderation
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Status: Moderation',
        header=f"This is to inform you that we have received your recently submitted project '{project.name}' for moderation. A moderator was assigned to review it.",
        actions=[{
            'text': 'View moderation state',
            'url': project.getModLink()
        }],
        footer=f"We'll notify you as soon as the moderator reviews your project submission. Till then, chill out! NOTE: We're lenient.",
        conclusion="This email was generated because we have received a project submission from your Knotters account. If this wasn't you, then please report to us."
    )



def sendProjectApprovedNotification(project: Project):
    """
    Project has been approved by moderator
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Status: Approved',
        header=f"Congratulations! Your submitted project '{project.name}' has been reviewed, and has been approved by the assigned moderator. " +
        "You can get more details on this by visiting the moderation page of your project submission.",
        actions=[{
            'text': 'View moderation',
            'url': project.getModLink()
        }],
        footer=f"Your project's profile page & other related setup will be available in a few moments. Cheers! The community at Knotters will be working together with you on {project.name}.",
        conclusion="This email was generated we have approved a project submission received from your Knotters account. If this is unfamiliar, then please report to us."
    )


def sendProjectRejectedNotification(project: Project):
    """
    Project has been rejected by moderator
    """
    return sendActionEmail(
        to=project.creator.getEmail(),
        username=project.creator.getFName(),
        subject='Project Status: Rejected',
        header=f"This is to inform you that your submitted project '{project.name}' has been reviewed, and unfortunately rejected by the assigned moderator. " +
        "You can get more details on this by visiting the moderation page of your project submission.",
        actions=[{
            'text': 'View moderation',
            'url': project.getModLink()
        }],
        footer=f"We don't generally reject projects, but if you think this is a mistake, then you can see if you can resubmit the same project for moderation. This is unfortunate.",
        conclusion="This email was generated we have rejected a project submission received from your Knotters account. If this is unfamiliar, then please report to us."
    )
