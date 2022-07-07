from django.core.handlers.wsgi import WSGIRequest
from main.constants import NotificationCode
from auth2.models import *
from main.env import PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail

from .models import (BaseProjectCoCreatorInvitation,
                     CoreModerationTransferInvitation, CoreProject,
                     CoreProjectDeletionRequest, FreeProject, FreeRepository, Project,
                     ProjectModerationTransferInvitation,
                     ProjectTransferInvitation, Snapshot, VerProjectDeletionRequest, BaseProject)
from main.methods import user_device_notify
from management.models import ReportCategory


def freeProjectCreated(project: FreeProject) -> str:
    """
    To notify creator for new free Project

    Args:
        project (FreeProject): Free Project instance that has been created

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.FREE_PROJ_CREATED).exists():
        device = user_device_notify(project.creator.user, "Project created",
                           f"Yay! You have successfully created a quick new project - {project.name} - on {PUBNAME}.",
                           project.getLink()
                           )

    if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.FREE_PROJ_CREATED).exists():
        email = sendActionEmail(
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
    return device, email

def freeProjectDeleted(project: FreeProject) -> str:
    """
    To notify creator for deleted free Project

    Args:
        project (FreeProject): Free Project instance that has been deleted

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.FREE_PROJ_DELETED).exists():
        device = user_device_notify(project.creator.user, "Project deleted",
                           f"Your project - {project.name} - has been deleted on {PUBNAME}, with all its associated data.")

    if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.FREE_PROJ_DELETED).exists():
        email = sendAlertEmail(
            to=project.creator.getEmail(),
            username=project.creator.getFName(),
            subject='Project Deleted',
            header=f"This is to inform you that your project - {project.name} ({project.nickname}) - has been deleted on {PUBNAME}, with all its associated data.",
            footer=f"You can always create a new project, whenever you like to start one.",
            conclusion=f"This email was sent because a project from your {PUBNAME} account was deleted. If this wasn't you, then please report to us."
        )
    return device, email


def sendProjectSubmissionNotification(verifiedproject: Project) -> str:
    """
    Verified Project has been submitted for moderation

    Args:
        verifiedproject (Project): Verified Project instance that has been submitted

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=verifiedproject.creator.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_SUBMITTED).exists():

        device = user_device_notify(verifiedproject.creator.user, "Project submitted for moderation",
                           f"We have received your recently submitted project - {verifiedproject.name} - for moderation. A moderator was assigned to review it.", verifiedproject.getModLink())

    if EmailNotificationSubscriber.objects.filter(user=verifiedproject.creator.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_SUBMITTED).exists():

        email = sendActionEmail(
            to=verifiedproject.creator.getEmail(),
            username=verifiedproject.creator.getFName(),
            subject='Project Status: Moderation',
            header=f"This is to inform you that we have received your recently submitted project - {verifiedproject.name} - for moderation. A moderator was assigned to review it.",
            actions=[{
                'text': 'View moderation state',
                'url': verifiedproject.getModLink()
            }],
            footer=f"We'll notify you as soon as the moderator reviews your project submission. Till then, chill out! NOTE: We're lenient.",
            conclusion=f"This email was sent because we have received a project submission from your Knotters account. If this wasn't you, then please report to us."
        )
    return device, email


def coreProjectSubmissionNotification(coreproject: CoreProject) -> str:
    """
    Core Project has been submitted for moderation

    Args:
        coreproject (CoreProject): Core Project instance that has been submitted

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=coreproject.creator.user, device_notification__notification__code=NotificationCode.CORE_PROJ_SUBMITTED).exists():
        device = user_device_notify(coreproject.creator.user, "Project submitted for moderation",
                           f"We have received your recently submitted core project request - {coreproject.name} - for moderation. Moderator has been assigned to review it.",
                           coreproject.getModLink())

    if EmailNotificationSubscriber.objects.filter(user=coreproject.creator.user, email_notification__notification__code=NotificationCode.CORE_PROJ_SUBMITTED).exists():
        email = sendActionEmail(
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
    return device, email


def sendProjectApprovedNotification(verifiedproject: Project) -> str:
    """
    Verified Project has been approved by moderator

    Args:
        verifiedproject (Project): Verified Project instance that has been approved

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=verifiedproject.creator.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_APPROVED).exists():
        device = user_device_notify(verifiedproject.creator.user, "Project Approved",
                           f"Congratulations! Your submitted project - {verifiedproject.name} - has been reviewed, and has been approved by the assigned moderator. ",
                           verifiedproject.getModLink())

    if EmailNotificationSubscriber.objects.filter(user=verifiedproject.creator.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_APPROVED).exists():
        email = sendActionEmail(
            to=verifiedproject.creator.getEmail(),
            username=verifiedproject.creator.getFName(),
            subject='Project Status: Approved',
            header=f"Congratulations! Your submitted project - {verifiedproject.name} - has been reviewed, and has been approved by the assigned moderator. " +
            "You can get more details on this by visiting the moderation page of your project submission.",
            actions=[{
                'text': 'View moderation',
                'url': verifiedproject.getModLink()
            }],
            footer=f"Your project's profile page & other related setup will be available in a few moments. Cheers! The moderator & community at {PUBNAME} will be working together with you on {verifiedproject.name}.",
            conclusion=f"This email was generated because a project submission received from your {PUBNAME} account has been approved. If this is unfamiliar, then please report to us."
        )
    return device, email


def sendCoreProjectApprovedNotification(project: CoreProject) -> str:
    """
    Core Project has been approved by moderator

    Args:
        project (CoreProject): Core Project instance that has been approved

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.CORE_PROJ_APPROVED).exists():
        device = user_device_notify(project.creator.user, "Project Approved",
                           f"Congratulations! Your submitted core project - {project.name} - has been reviewed, and has been approved by the assigned moderator.",
                           project.getModLink())

    if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.CORE_PROJ_APPROVED).exists():
        email = sendActionEmail(
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
    return device, email


def projectRejectedNotification(verifiedproject: Project) -> str:
    """
    Verified Project has been rejected by moderator

    Args:
        verifiedproject (Project): Verified Project instance that has been rejected

    Returns:
        str: task ID of email task
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=verifiedproject.creator.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_REJECTED).exists():
        device = user_device_notify(verifiedproject.creator.user, "Project Rejected",
                           f"Your submitted project - {verifiedproject.name} - has been reviewed, and unfortunately rejected by the assigned moderator. ",
                           verifiedproject.getLink())

    if EmailNotificationSubscriber.objects.filter(user=verifiedproject.creator.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_REJECTED).exists():
        email = sendActionEmail(
            to=verifiedproject.creator.getEmail(),
            username=verifiedproject.creator.getFName(),
            subject='Project Status: Rejected',
            header=f"This is to inform you that your submitted project - {verifiedproject.name} - has been reviewed, and unfortunately rejected by the assigned moderator. " +
            "You can get more details on this by visiting the moderation page of your project submission.",
            actions=[{
                'text': 'View moderation',
                'url': verifiedproject.getLink()
            }],
            footer=f"The moderator must have found something unacceptable, but if you think this is a mistake, then you might be able to resubmit the same project for moderation. This is unfortunate.",
            conclusion=f"This email was generated we have rejected a project submission received from your {PUBNAME} account. If this is unfamiliar, then please report to us."
        )
    return device, email


def projectTransferInvitation(invite: ProjectTransferInvitation) -> str:
    """
    To send invitation to receiver for project ownership

    Args:
        invite (ProjectTransferInvitation): ProjectTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if invite.resolved or invite.expired:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.PROJ_TRANSFER_INVITE).exists():
        device = user_device_notify(invite.receiver.user, "Project Transfer Invitation",
                           f"You've been invited to accept ownership of project {invite.baseproject.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
                           invite.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.PROJ_TRANSFER_INVITE).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.PROJ_TRANSFER_INVITE).exists():
        device1 = user_device_notify(invite.sender.user, "Project Transfer Initiated",
                           f"You've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept ownership of your project {invite.baseproject.name}.",
                           invite.baseproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.PROJ_TRANSFER_INVITE).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def projectTransferAcceptedInvitation(invite: ProjectTransferInvitation) -> str:
    """
    To notify sender & receiver about acceptence of project ownership

    Args:
        invite (ProjectTransferInvitation): ProjectTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.PROJ_TRANSFER_ACCEPTED).exists():
        device = user_device_notify(invite.sender.user, "Project Tranfer Success",
                           f"Your project, {invite.baseproject.name}, has been successfully transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
                           invite.baseproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.PROJ_TRANSFER_ACCEPTED).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.PROJ_TRANSFER_ACCEPTED).exists():
        device1 = user_device_notify(invite.receiver.user, "Project Ownership Accepted",
                           f"You've accepted the ownership of {invite.baseproject.name}.",
                           invite.baseproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.PROJ_TRANSFER_ACCEPTED).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def projectTransferDeclinedInvitation(invite: ProjectTransferInvitation) -> str:
    """
    To notify sender about decline of project ownership

    Args:
        invite (ProjectTransferInvitation): ProjectTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.PROJ_TRANSFER_DECLINED).exists():
        device = user_device_notify(invite.sender.user, "Project Transfer Failed",
                           f"Your project, {invite.baseproject.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}) as the invite was rejected.",
                           invite.baseproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.PROJ_TRANSFER_DECLINED).exists():
        email = sendActionEmail(
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
    return device, email


def projectModTransferInvitation(invite: ProjectModerationTransferInvitation) -> str:
    """
    To send invitation to receiver and notify sender about project moderatorship transfer

    Args:
        invite (ProjectModerationTransferInvitation): ProjectModerationTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if invite.resolved or invite.expired:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER).exists():
        device = user_device_notify(invite.receiver.user, "Verified Project Moderation Transfer Invite",
                           f"You've been invited to accept moderatorship of verified project {invite.project.name} by its current moderator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
                           invite.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER).exists():
        device1 = user_device_notify(invite.sender.user, "Verified Project Moderation Transfer Initiated",
                           f"You've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept moderatorship of the verified project {invite.project.name}.",
                           invite.project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def projectModTransferAcceptedInvitation(invite: ProjectModerationTransferInvitation):
    """
    To notify sender & receiver about acceptence of project moderatorship

    Args:
        invite (ProjectModerationTransferInvitation): ProjectModerationTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER_ACCEPTED).exists():
        device = user_device_notify(invite.sender.user, "Verified Project Moderation Transfer Success",
                           f"Your moderatorship of the verified project, {invite.project.name}, has been successfully transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
                           invite.project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER_ACCEPTED).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER_ACCEPTED).exists():
        device1 = user_device_notify(invite.receiver.user, "Verified Project Moderation Accepted",
                           f"You've accepted the moderatorship of {invite.project.name}.",
                           invite.project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER_ACCEPTED).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def projectModTransferDeclinedInvitation(invite: ProjectModerationTransferInvitation) -> str:
    """
    To notify sender about decline of project moderatorship

    Args:
        invite (ProjectModerationTransferInvitation): ProjectModerationTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER_REJECTED).exists():
        device = user_device_notify(invite.sender.user, "Verified Project Moderation Transfer Failed",
                           f"Your moderatorship of the verified project, {invite.project.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}) as the invite was rejected.",
                           invite.project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.PROJ_MOD_TRANSFER_REJECTED).exists():
        email = sendActionEmail(
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
    return device, email


def coreProjectModTransferInvitation(invite: CoreModerationTransferInvitation) -> str:
    """
    To send invitation to receiver and notify sender about core project moderatorship transfer

    Args:
        invite (CoreModerationTransferInvitation): CoreModerationTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if invite.resolved or invite.expired:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER).exists():
        device = user_device_notify(invite.receiver.user, "Core Project Moderation Transfer Invite",
                           f"You've been invited to accept moderatorship of core project {invite.coreproject.name} by its current moderator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
                           invite.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER).exists():
        email = sendActionEmail(
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
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER).exists():
        device1 = user_device_notify(invite.sender.user, "Core Project Moderation Transfer Initiated",
                           f"You've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept moderatorship of the core project {invite.coreproject.name}.",
                           invite.coreproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def coreProjectModTransferAcceptedInvitation(invite: CoreModerationTransferInvitation) -> str:
    """
    To notify sender & receiver about acceptence of core project moderatorship

    Args:
        invite (CoreModerationTransferInvitation): CoreModerationTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER_ACCEPTED).exists():
        device = user_device_notify(invite.sender.user, "Core Project Moderation Transfer Success",
                           f"Your moderatorship of the core project, {invite.coreproject.name}, has been successfully transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
                           invite.coreproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER_ACCEPTED).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER_ACCEPTED).exists():
        device1 = user_device_notify(invite.receiver.user, "Core Project Moderation Accepted",
                           f"You've accepted the moderatorship of {invite.coreproject.name}.",
                           invite.coreproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER_ACCEPTED).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def coreProjectModTransferDeclinedInvitation(invite: CoreModerationTransferInvitation) -> str:
    """
    To notify sender about decline of core project moderatorship

    Args:
        invite (CoreModerationTransferInvitation): CoreModerationTransferInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER_REJECTED).exists():
        device = user_device_notify(invite.sender.user, "Core Project Moderation Transfer Failed",
                           f"Your moderatorship of the core project, {invite.coreproject.name}, has not been transferred to {invite.receiver.getName()} ({invite.receiver.getEmail()}) as the invite was rejected.",
                           invite.coreproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CORE_PROJ_MOD_TRANSFER_REJECTED).exists():
        email = sendActionEmail(
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
    return device, email


def verProjectDeletionRequest(invite: VerProjectDeletionRequest) -> str:
    """
    To notify sender & receiver about deletion request of verified project

    Args:
        invite (VerProjectDeletionRequest): VerProjectDeletionRequest instance

    Returns:
        str: task ID of email task
    """
    if invite.resolved or invite.expired:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION).exists():
        device = user_device_notify(invite.receiver.user, "Verified Project Deletion Request",
                           f"You've been requested to delete the verified project {invite.project.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
                           invite.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION).exists():
        device1 = user_device_notify(invite.sender.user, "Verified Project Deletion Requested",
                           f"You've requested {invite.receiver.getName()} ({invite.receiver.getEmail()}) to delete the verified project {invite.project.name}.",
                           invite.project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def verProjectDeletionAcceptedRequest(invite: VerProjectDeletionRequest) -> str:
    """
    To notify sender & receiver about acceptence of verified project deletion request

    Args:
        invite (VerProjectDeletionRequest): VerProjectDeletionRequest instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION_ACCEPTED).exists():
        device = user_device_notify(invite.sender.user, "Verified Project Deletion Accepted",
                           f"Your request to delete the verified project, {invite.project.name}, has been accepted by {invite.receiver.getName()} ({invite.receiver.getEmail()}).")

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION_ACCEPTED).exists():
        email = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Verified Project Deletion Accepted",
            header=f"This is to inform you that your request to delete the verified project, {invite.project.name}, has been accepted by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
            footer=f"This action was irreversible, and the project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon.",
            conclusion=f"This email was sent because you had requested deletion of a verified project."
        )

    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION_ACCEPTED).exists():
        device1 = user_device_notify(invite.receiver.user, "Verified Project Deletion Accepted",
                           f"You've accepted to delete the verified project {invite.project.name}.")

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION_ACCEPTED).exists():
        email1 = sendActionEmail(
            to=invite.receiver.getEmail(),
            username=invite.receiver.getFName(),
            subject=f"Verified Project Deletion Accepted",
            header=f"This is to inform you that you've accepted to delete the verified project {invite.project.name}.",
            footer=f"The project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon. This action was irreversible, as you should know already.",
            conclusion=f"This email was sent because you've deleted a verified project."
        )
    return device, email, device1, email1


def verProjectDeletionDeclinedRequest(invite: VerProjectDeletionRequest) -> str:
    """
    To notify sender about decline of verified project deletion request

    Args:
        invite (VerProjectDeletionRequest): VerProjectDeletionRequest instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION_REJECTED).exists():
        device = user_device_notify(invite.sender.user, "Verified Project Deletion Failed",
                           f"Your deletion of the verified project, {invite.project.name}, has been rejected by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
                           invite.project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.VERIF_PROJ_DELETION_REJECTED).exists():
        email = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Verified Project Deletion Failed",
            header=f"This is to inform you that your deletion of the verified project, {invite.project.name}, has not been accepted {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
            actions=[{
                'text': 'View Verified Project',
                'url': invite.project.get_link
            }],
            footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def coreProjectDeletionRequest(invite: CoreProjectDeletionRequest) -> str:
    """
    To notify sender & receiver about deletion request of core project

    Args:
        invite (CoreProjectDeletionRequest): CoreProjectDeletionRequest instance

    Returns:
        str: task ID of email task
    """
    if invite.resolved or invite.expired:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.CORE_PROJ_DELETION).exists():
        device = user_device_notify(invite.receiver.user, "Core Project Deletion Request",
                           f"You've been requested to delete the core project {invite.coreproject.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
                           invite.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.CORE_PROJ_DELETION).exists():
        email = sendActionEmail(
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

    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CORE_PROJ_DELETION).exists():
        device1 = user_device_notify(invite.sender.user, "Core Project Deletion Requested",
                           f"You've requested {invite.receiver.getName()} ({invite.receiver.getEmail()}) to delete the core project {invite.coreproject.name}.",
                           invite.coreproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CORE_PROJ_DELETION).exists():
        email1 = sendActionEmail(
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
    return device, email, device1, email1


def coreProjectDeletionAcceptedRequest(invite: CoreProjectDeletionRequest) -> str:
    """
    To notify sender & receiver about acceptence of core project deletion request

    Args:
        invite (CoreProjectDeletionRequest): CoreProjectDeletionRequest instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CORE_PROJ_DELETION_ACCEPTED).exists():
        device = user_device_notify(invite.sender.user, "Core Project Deletion Accepted",
                           f"Your request to delete the core project, {invite.coreproject.name}, has been accepted by {invite.receiver.getName()} ({invite.receiver.getEmail()}).")

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CORE_PROJ_DELETION_ACCEPTED).exists():
        email = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Core Project Deletion Accepted",
            header=f"This is to inform you that your request to delete the core project, {invite.coreproject.name}, has been accepted by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
            footer=f"This action was irreversible, and the project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon.",
            conclusion=f"This email was sent because you had requested deletion of a core project."
        )

    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.CORE_PROJ_DELETION_ACCEPTED).exists():
        device1 = user_device_notify(invite.receiver.user, "Core Project Deletion Accepted",
                           f"You've accepted to delete the core project {invite.coreproject.name}.")

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.CORE_PROJ_DELETION_ACCEPTED).exists():
        email1 = sendActionEmail(
            to=invite.receiver.getEmail(),
            username=invite.receiver.getFName(),
            subject=f"Core Project Deletion Accepted",
            header=f"This is to inform you that you've accepted to delete the core project {invite.coreproject.name}.",
            footer=f"The project will no longer exist on {PUBNAME}, and all related assets, repositories and teams will be deleted soon. This action was irreversible, as you should know already.",
            conclusion=f"This email was sent because you've deleted a core project."
        )
    return device, email, device1, email1


def coreProjectDeletionDeclinedRequest(invite: CoreProjectDeletionRequest) -> str:
    """
    To notify sender about decline of core project deletion request

    Args:
        invite (CoreProjectDeletionRequest): CoreProjectDeletionRequest instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CORE_PROJ_DELETION_REJECTED).exists():
        device = user_device_notify(invite.sender.user, "Core Project Deletion Failed",
                           f"Your request for deletion of the core project, {invite.coreproject.name}, has been rejected by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
                           invite.coreproject.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CORE_PROJ_DELETION_REJECTED).exists():
        email = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Core Project Deletion Failed",
            header=f"This is to inform you that your request for deletion of the core project, {invite.coreproject.name}, has been rejected by {invite.receiver.getName()} ({invite.receiver.getEmail()}).",
            actions=[{
                'text': 'View Core Project',
                'url': invite.coreproject.get_link
            }],
            footer=f"This is because your invited person have rejected this invitation. You can re-invite them or anyone again.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def baseProjectCoCreatorInvitation(invite: BaseProjectCoCreatorInvitation) -> str:
    """
    To notify sender & receiver about invitation for co-creatorship of base project

    Args:
        invite (BaseProjectCoCreatorInvitation): BaseProjectCoCreatorInvitation instance

    Returns:
        str: task ID of email task
    """
    if invite.resolved or invite.expired:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.CO_BASE_PROJECT).exists():
        device = user_device_notify(invite.receiver.user, "Project Co-Creator Invite",
                           f"You've been invited to accept co-creatorship of the project {invite.base_project.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
                           invite.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.CO_BASE_PROJECT).exists():
        email = sendActionEmail(
            to=invite.receiver.getEmail(),
            username=invite.receiver.getFName(),
            subject=f"Project Co-Creator Invite",
            header=f"You've been invited to accept co-creatorship of the project {invite.base_project.name} by its creator, {invite.sender.getName()} ({invite.sender.getEmail()}).",
            actions=[{
                'text': 'View Invitation',
                'url': invite.get_link
            }],
            footer=f"Visit the above link to decide whether you'd want to be a co-creator of the project.",
            conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make your decision there."
        )

    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CO_BASE_PROJECT).exists():
        device1 = user_device_notify(invite.sender.user, "Project Co-Creator Invited",
                           f"You've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept co-creatorship of your project {invite.base_project.name}.",
                           invite.base_project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CO_BASE_PROJECT).exists():
        email1 = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Project Co-Creator Invited",
            header=f"This is to inform you that you've invited {invite.receiver.getName()} ({invite.receiver.getEmail()}) to accept co-creatorship of your project {invite.base_project.name}.",
            actions=[{
                'text': 'View project',
                'url': invite.base_project.get_link
            }],
            footer=f"If they decline, then they will not be added as a co-creator.",
            conclusion=f"If this action is unfamiliar, then you should delete the co-creator invite by visiting your project's profile."
        )
    return device, email, device1, email1


def baseProjectCoCreatorAcceptedInvitation(invite: BaseProjectCoCreatorInvitation) -> str:
    """
    To notify sender & receiver about acceptence of co-creatorship of base project

    Args:
        invite (BaseProjectCoCreatorInvitation): BaseProjectCoCreatorInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email, device1, email1 = False, False, False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CO_BASE_PROJECT_ACCEPTED).exists():
        device = user_device_notify(invite.sender.user, "Project Co-creator Invite Success",
                           f"{invite.receiver.getName()} ({invite.receiver.getEmail()}) has been successfully added as a co-creator in your project, {invite.base_project.name}.",
                           invite.base_project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CO_BASE_PROJECT_ACCEPTED).exists():
        email = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Project Co-creator Invite Success",
            header=f"This is to inform you that {invite.receiver.getName()} ({invite.receiver.getEmail()}) has been successfully added as a co-creator in your project, {invite.base_project.name}.",
            actions=[{
                'text': 'View project',
                'url': invite.base_project.get_link
            }],
            footer=f"Now they can also edit and make changes to your project as a co-creator.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )

    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.CO_BASE_PROJECT_ACCEPTED).exists():
        device1 = user_device_notify(invite.receiver.user, "Project Co-Creatorship Accepted",
                           f"You've accepted the co-creatorship of {invite.base_project.name}.",
                           invite.base_project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.CO_BASE_PROJECT_ACCEPTED).exists():
        email1 = sendActionEmail(
            to=invite.receiver.getEmail(),
            username=invite.receiver.getFName(),
            subject=f"Project Co-Creatorship Accepted",
            header=f"This is to inform you that you've accepted the co-creatorship of {invite.base_project.name}.",
            actions=[{
                'text': 'View Project',
                'url': invite.base_project.get_link
            }],
            footer=f"Now you have the control and will be shown as co-creator of the project at {PUBNAME}.",
            conclusion=f"This email was sent because you've accepted the project's co-creatorship."
        )
    return device, email, device1, email1


def baseProjectCoCreatorDeclinedInvitation(invite: BaseProjectCoCreatorInvitation) -> str:
    """
    To notify sender & receiver about decline of co-creatorship of base project

    Args:
        invite (BaseProjectCoCreatorInvitation): BaseProjectCoCreatorInvitation instance

    Returns:
        str: task ID of email task
    """
    if not invite.resolved:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=invite.sender.user, device_notification__notification__code=NotificationCode.CO_BASE_PROJECT_REJECTED).exists():
        device = user_device_notify(invite.sender.user, "Project Co-Creatorship Invite Declined",
                           f"Your invitation to {invite.receiver.getName()} ({invite.receiver.getEmail()}) for the co-creatorship of the project, {invite.base_project.name}, has been declined.",
                           invite.base_project.get_link)

    if EmailNotificationSubscriber.objects.filter(user=invite.sender.user, email_notification__notification__code=NotificationCode.CO_BASE_PROJECT_REJECTED).exists():
        email = sendActionEmail(
            to=invite.sender.getEmail(),
            username=invite.sender.getFName(),
            subject=f"Project Co-Creatorship Invite Declined",
            header=f"This is to inform you that your invitation to {invite.receiver.getName()} ({invite.receiver.getEmail()}) for the co-creatorship of the project, {invite.base_project.name}, has been declined.",
            actions=[{
                'text': 'View Project',
                'url': invite.base_project.get_link
            }],
            footer=f"This is because the invited person has rejected the invitation. You can re-invite them or anyone again.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def reportedProject(project: BaseProject, category: ReportCategory):
    """
    To notify creator of project that their project has been reported
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.REPORTED_PROJECT).exists():
        device = user_device_notify(project.creator.user, "Project Reported",
                           f"Your project - {project.name} - has been reported for {category}. The complaint is under review.",
                           project.getLink())
    if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.REPORTED_PROJECT).exists():
        email = sendActionEmail(
            to=project.creator.get_email, username=project.creator.user.first_name, subject='Project Reported for violation of rules',
            header=f"This is to inform you that your project - {project.name} - has been reported for {category}. The report is under review.",
            actions=[{'text': "View Project",
                      'url': project.getLink()}],
            footer=f"Knotters is a place for creating community and belonging. To avoid future reports against you, make sure you read and understand Knotters terms and conditions.",
            conclusion=f"If you think this is a mistake, please report to us."
        )
    return device, email


def projectAdmired(request: WSGIRequest, project: BaseProject):
    """
    To notify creator of project that someone has admired their project
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.ADMIRED_PROJECT).exists():
        if(project.is_free() and project.getProject().is_submission()):
            device = user_device_notify(project.creator.user, "Project Admired",
                               f"Your project - {project.name} - which is a submission of - {project.getProject().submission().competition.title} - competition has been admired by {request.user.first_name}",
                               project.getLink(),
                               actions=[{
                                   'title': 'View Project',
                                   'url': project.get_link,
                                   'action': "action1"},
                                   {'title': 'View Competition',
                                    'url': project.getProject().submission().competition.getLink(),
                                    'action': "action2"}])
        else:
            device = user_device_notify(project.creator.user, "Project Admired",
                               f"Your project - {project.name} - has been admired by {request.user.first_name}",
                               project.getLink())

    if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.ADMIRED_PROJECT).exists():
        if(project.is_free() and project.getProject().is_submission()):
            email = sendActionEmail(
                to=project.creator.getEmail(),
                username=project.creator.getFName(),
                subject=f"Project Admired",
                header=f"This is to inform you that your project - {project.name} - which is a submission of - {project.getProject().submission().competition.title} - competition has been admired by {request.user.first_name}.",
                actions=[{
                    'text': 'View Project',
                    'url': project.get_link
                },
                    {
                    'text': 'View Competition',
                    'url': project.getProject().submission().competition.getLink()
                }],
                footer=f"You can thank and reach out to {request.user.first_name}.",
                conclusion=f"If this action is unfamiliar, then you may contact us."
            )
        else:
            email = sendActionEmail(
                to=project.creator.getEmail(),
                username=project.creator.getFName(),
                subject=f"Project Admired",
                header=f"This is to inform you that your project - {project.name} - has been admired by {request.user.first_name}.",
                actions=[{
                    'text': 'View Project',
                    'url': project.get_link
                }],
                footer=f"You can thank and reach out to {request.user.first_name}.",
                conclusion=f"If this action is unfamiliar, then you may contact us."
            )
    return device, email


def snapshotAdmired(request: WSGIRequest, snap: Snapshot):
    """
    To notify creator of snapshot that someone has admired their snapshot
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=snap.creator.user, device_notification__notification__code=NotificationCode.ADMIRED_SNAPSHOT).exists():
        device = user_device_notify(snap.creator.user, "Snapshot Admired",
                           f"Your snapshot of project - {snap.base_project.name} - has been admired by - {request.user.first_name}",
                           snap.getLink())

    if EmailNotificationSubscriber.objects.filter(user=snap.creator.user, email_notification__notification__code=NotificationCode.ADMIRED_SNAPSHOT).exists():
        email = sendActionEmail(
            to=snap.creator.getEmail(),
            username=snap.creator.getFName(),
            subject=f"Snapshot Admired",
            header=f"This is to inform you that your snapshot of project - {snap.base_project.name} - has been admired by - {request.user.first_name}.",
            actions=[{
                'text': 'View Snapshot',
                'url': snap.get_link
            }],
            footer=f"You can thank and reach out to {request.user.first_name}.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def snapshotCreated(project: BaseProject, snap: Snapshot):
    """
    To notify creator, moderator and mentor when snapshot is posted in their project
    """
    done = []
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=snap.creator.user, device_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
        device = user_device_notify(snap.creator.user, "Snapshot Created",
                           f"You have sucessfully created snapshot for your project - {project.name} - ",
                           snap.getLink())

    if EmailNotificationSubscriber.objects.filter(user=snap.creator.user, email_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
        email = sendActionEmail(
            to=snap.creator.getEmail(),
            username=snap.creator.getFName(),
            subject=f"Snapshot Created",
            header=f"This is to inform you that you have sucessfully created snapshot for your project - {project.name} - .",
            actions=[{
                'text': 'View Snapshot',
                'url': snap.get_link
            }],
            footer=f"You can create more snapshots for your project.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    done.append([device, email])

    device_c, email_c = False, False
    if(project.creator != snap.creator):
        if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
            device_c = user_device_notify(project.creator.user, "Snapshot Created",
                               f"Snapshot has been created for your project - {project.name} - by {snap.creator.getFName()}",
                               snap.getLink())

        if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
            email_c = sendActionEmail(
                to=project.creator.getEmail(),
                username=project.creator.getFName(),
                subject=f"Snapshot Created",
                header=f"This is to inform you that snapshot has been created for your project - {project.name} - by {snap.creator.getFName()}",
                actions=[{
                    'text': 'View Snapshot',
                    'url': snap.get_link
                }],
                footer=f"You can also create more snapshots for your project. You are receiving this mail because you are creator of this project. ",
                conclusion=f"If this action is unfamiliar, then you may contact us."
            )
        done.append([device_c, email_c])

    device_m, email_m = False, False
    if(project.get_moderator() and project.get_moderator() != snap.creator):
        moderator = project.get_moderator()
        if DeviceNotificationSubscriber.objects.filter(user=moderator.user, device_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
            device_m = user_device_notify(moderator.user, "Snapshot Created",
                               f"Snapshot has been created for your moderated project - {project.name} - by {snap.creator.getFName()}",
                               snap.getLink())

        if EmailNotificationSubscriber.objects.filter(user=moderator.user, email_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
            email_m = sendActionEmail(
                to=moderator.getEmail(),
                username=moderator.getFName(),
                subject=f"Snapshot Created",
                header=f"This is to inform you that snapshot has been created for your moderated project - {project.name} - by {snap.creator.getFName()}",
                actions=[{
                    'text': 'View Snapshot',
                    'url': snap.get_link
                }],
                footer=f"You can also create more snapshots for your project. You are receiving this mail because you are moderator of this project. ",
                conclusion=f"If this action is unfamiliar, then you may contact us."
            )
        done.append([device_m, email_m])

    device_mn, email_mn = False, False
    if(project.get_mentor() and project.get_mentor() != snap.creator):
        mentor = project.get_mentor()
        if DeviceNotificationSubscriber.objects.filter(user=mentor.user, device_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
            device_mn = user_device_notify(mentor.user, "Snapshot Created",
                               f"Snapshot has been created for your mentored project - {project.name} - by {snap.creator.getFName()}",
                               snap.getLink())

        if EmailNotificationSubscriber.objects.filter(user=mentor.user, email_notification__notification__code=NotificationCode.SNAPSHOT_CREATED).exists():
            email_mn = sendActionEmail(
                to=mentor.getEmail(),
                username=mentor.getFName(),
                subject=f"Snapshot Created",
                header=f"This is to inform you that snapshot has been created for your mentored project - {project.name} - by {snap.creator.getFName()}",
                actions=[{
                    'text': 'View Snapshot',
                    'url': snap.get_link
                }],
                footer=f"You can also create more snapshots for your project. You are receiving this mail because you are mentor of this project. ",
                conclusion=f"If this action is unfamiliar, then you may contact us."
            )
        done.append([device_mn, email_mn])
    return done

def reportedSnapshot(snap: Snapshot, category: ReportCategory):
    """
    To notify creator of snapshot that their snapshot has been reported
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=snap.creator.user, device_notification__notification__code=NotificationCode.REPORTED_SNAPSHOT).exists():
        device = user_device_notify(snap.creator.user, "Snapshot Reported",
                           f"Your snapshot of project - {snap.base_project.name} - has been reported for {category}. The complaint is under review.",
                           snap.getLink())
    if EmailNotificationSubscriber.objects.filter(user=snap.creator.user, email_notification__notification__code=NotificationCode.REPORTED_SNAPSHOT).exists():
        email = sendActionEmail(
            to=snap.creator.get_email, username=snap.creator.getFName(), subject='Snapshot Reported for violation of rules',
            header=f"This is to inform you that your snapshot of project - {snap.base_project.name} - has been reported for {category}. The report is under review.",
            actions=[{'text': "View Snapshot",
                      'url': snap.getLink()}],
            footer=f"Knotters is a place for creating community and belonging. To avoid future reports against your content, make sure you read and understand Knotters terms and conditions.",
            conclusion=f"If you think this is a mistake, please report to us."
        )
    return device, email


def githubBotInstalled(frepos):
    """
    To notify creator of project that knotters github bot has been installed to their linked github repository
    """
    done = []
    for frepo in frepos:
        device, email = False, False
        project = frepo.free_project
        if DeviceNotificationSubscriber.objects.filter(user=project.creator.user, device_notification__notification__code=NotificationCode.GITHUB_BOT_INSTALLED).exists():
            device = user_device_notify(project.creator.user, "Github Bot Installed",
                               f"Knotters Github bot has been installed in repository linked to your project {project.name}.",
                               project.getLink(),
                               actions=[{
                                   'title': 'View Project',
                                   'url': project.get_link,
                                   'action': "action1"},
                                   {'title': 'View Repository',
                                    'url': frepo.repolink(),
                                    'action': "action2"}])
        if EmailNotificationSubscriber.objects.filter(user=project.creator.user, email_notification__notification__code=NotificationCode.GITHUB_BOT_INSTALLED).exists():
            email = sendActionEmail(
                to=project.creator.get_email, username=project.creator.getFName(), subject='Knotters Github Bot Installed',
                header=f"This is to inform you that Knotters Github bot has been installed in repository linked to project {project.name}.",
                actions=[{'text': "View Project",
                          'url': project.getLink()},
                         {'text': "View Repository",
                         'url': frepo.repolink()}],
                footer=f"You are receiving this mail because Knotters Github bot has been installed in the repository linked to a project which is created by you.",
                conclusion=f"If you think this is a mistake, please report to us."
            )
        done.append([device, email])
    return done
        
