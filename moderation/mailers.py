from main.env import PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail
from main.strings import COMPETE, CORE_PROJECT, PEOPLE, PROJECTS
from people.models import Profile
from auth2.models import DeviceNotificationSubscriber, EmailNotificationSubscriber
from .models import Moderation
from main.constants import NotificationCode
from main.methods import user_device_notify


def moderationAssignedAlert(moderation: Moderation) -> str:
    """Sends an email to the moderator that they have been assigned a moderation.

    Args:
        moderation (Moderation): The moderation that has been assigned.

    Returns:
        str: task ID of the email task.
        bool: False if the email was not sent.
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=moderation.moderator.user, device_notification__notification__code=NotificationCode.MODERATION_ASSIGNED).exists():
        device = user_device_notify(moderation.moderator.user, "New Moderation Assigned",
                           f"A new {['project', 'competition', 'person', 'core project'][[PROJECTS, COMPETE, PEOPLE, CORE_PROJECT].index(moderation.type)]} moderation has been assigned to you to review. The following link button will take you directly to the moderation view.", moderation.getLink())
    if EmailNotificationSubscriber.objects.filter(user=moderation.moderator.user, email_notification__notification__code=NotificationCode.MODERATION_ASSIGNED).exists():
        email = sendActionEmail(
            to=moderation.moderator.getEmail(),
            username=moderation.moderator.getName(),
            subject="New Moderation Assigned",
            header=f"A new {['project', 'competition', 'person', 'core project'][[PROJECTS, COMPETE, PEOPLE, CORE_PROJECT].index(moderation.type)]} moderation has been assigned to you to review. The following link button will take you directly to the moderation view.",
            actions=[{
                'text': 'View moderation',
                'url': moderation.getLink()
            }],
            footer=f"Take action only after thoroughly reviewing this moderation. This moderation will become stale in {moderation.stale_days} days if not responded.",
            conclusion=f"You received this email because you're a moderator at {PUBNAME}. If this is an error, please report to us."
        )
    return device, email


def moderationActionAlert(moderation: Moderation, status: str) -> str:
    """Sends an email to the moderator notifying them of a their moderation action.

    Args:
        moderation (Moderation): The moderation that has been assigned.
        status (str): The status of the moderation.

    Returns:
        str: task ID of the email task.
        bool: False if the email was not sent.

    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=moderation.moderator.user, device_notification__notification__code=NotificationCode.MODERATION_ACTION).exists():
        device = user_device_notify(moderation.moderator.user, f"Moderation {status.capitalize()}",
                           f"This is to inform you that a {['project', 'competition', 'person', 'core project'][[PROJECTS, COMPETE, PEOPLE, CORE_PROJECT].index(moderation.type)]} moderation has been {status} by you as the assigned moderator.", moderation.getLink())
    if EmailNotificationSubscriber.objects.filter(user=moderation.moderator.user, email_notification__notification__code=NotificationCode.MODERATION_ACTION).exists():
        email = sendAlertEmail(
            to=moderation.moderator.getEmail(),
            username=moderation.moderator.getFName(),
            subject=f"Moderation {status.capitalize()}",
            header=f"This is to inform you that a {['project', 'competition', 'person', 'core project'][[PROJECTS, COMPETE, PEOPLE, CORE_PROJECT].index(moderation.type)]} moderation has been {status} by you as the assigned moderator.",
            actions=[{
                'text': 'View moderation',
                'url': moderation.getLink()
            }],
            footer="If you acknowledge this action, then this email can be ignored safely.",
            conclusion=f"You received this email because you're a moderator at {PUBNAME}. If this is an error, please report to us."
        )
    return device, email


def madeModeratorAlert(profile: Profile) -> str:
    """Sends an email to the user notifying them that they have been promoted to moderator.

    Args:
        profile (Profile): The profile that has been promoted.

    Returns:
        str: task ID of the email task.
        bool: False if the email was not sent.
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.MODERATION_ACTION).exists():
        device = user_device_notify(profile.user, "Promotion to Moderator",
                           f"Congratulations! You have been made one of our moderators. This brings previleges and duties with rewards! The following link button will brief you as a moderator.", '/docs/moderationguidelines')
    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.UPGRADE_MODERATOR).exists():
        email = sendActionEmail(
            to=profile.getEmail(),
            username=profile.getFName(),
            subject=f"Promotion to Moderator",
            header=f"Congratulations! You have been made one of our moderators. This brings previleges and duties with rewards! The following link button will brief you as a moderator.",
            actions=[{
                'text': "Get started",
                'url': '/docs/moderationguidelines'
            }],
            footer=f"It's fun and rewarding to be a moderator at {PUBNAME}, and we wish you loads of luck with your adventure lying ahead!",
            conclusion=f"You received this email because you've been made a moderator at {PUBNAME}. You can always withdraw from this previlege via your account settings."
        )
    return device, email
