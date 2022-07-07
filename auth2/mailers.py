from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.core.handlers.wsgi import WSGIRequest
from main.env import PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail
from main.strings import url
from people.models import Profile, User
from .apps import APPNAME
from .models import EmailNotificationSubscriber, DeviceNotificationSubscriber
from main.constants import NotificationCode
from main.methods import user_device_notify


def passwordChangeAlert(user: User) -> str:
    device, email = False, False
    device = user_device_notify(user, "Account Password Changed",
                       f"This is to inform you that your {PUBNAME} account ({user.email}) password was changed recently."
                       )

    email = sendAlertEmail(to=user.email, username=user.first_name, subject='Account Password Changed',
                   header=f"This is to inform you that your {PUBNAME} account ({user.email}) password was changed recently.",
                   footer="If you acknowledge this action, then this email can be ignored safely.",
                   conclusion=f"If this action is suspicious and you didn't do such thing, then immediately head on to {PUBNAME} and request a password reset by choosing 'forgot' on login."
                   )
    return device, email


def emailUpdateAlert(user: User, oldEmail: str, newEmail: str) -> str:
    device, email = False, False
    if EmailAddress.objects.filter(user=user, verified=True).exists():
        device = user_device_notify(user, "Primary Email Address Changed",
                           f"This is to inform you that your {PUBNAME} primary email address was changed from {oldEmail} to {newEmail}, recently."
                           )

    if EmailNotificationSubscriber.objects.filter(user=user, email_notification__notification__code=NotificationCode.EMAIL_UPDATE).    exists():
        email = sendAlertEmail(to=oldEmail, username=user.first_name, subject='Primary Email Address Changed',
                       header=f"This is to inform you that your {PUBNAME} primary email address was changed from {oldEmail} to {newEmail}, recently.",
                       footer="If you acknowledge this action, then this email can be ignored safely.",
                       conclusion=f"If this action is suspicious and you didn't do such thing, then please report to us. Your {PUBNAME} account may have been compromised."
                       )
    return device, email


def emailAddAlert(user: User, newEmail: str) -> str:
    device, email = False, False
    if EmailAddress.objects.filter(user=user, verified=True).exists():
        device = user_device_notify(user, "New Email Address Added",
                           f"This is to inform you that a new email address ({newEmail}) was added to your {PUBNAME} account, recently."
                           )

        email = sendAlertEmail(to=user.email, username=user.first_name, subject='New Email Address Added',
                       header=f"This is to inform you that a new email address ({newEmail}) was added to your {PUBNAME} account, recently. This however, will NOT affect your existing ({user.email}) login email address.",
                       footer="If you acknowledge this action, then this email can be ignored safely.",
                       conclusion=f"If this action is suspicious and you didn't do such thing, then immediately login to {PUBNAME} and remove this new email address from your acccount."
                       )
    return device, email


def emailRemoveAlert(user: User, removedEmail: str) -> str:
    device, email = False, False
    if EmailAddress.objects.filter(user=user, verified=True).exists():
        device = user_device_notify(user, "New Email Address Removed",
                           f"This is to inform you that an email address ({removedEmail}) was removed from your {PUBNAME} account."
                           )

        email = sendAlertEmail(to=user.email, username=user.first_name, subject='Email Address Removed',
                       header=f"This is to inform you that an email address ({removedEmail}) was removed from your {PUBNAME} account.",
                       footer="If you acknowledge this action, then this email can be ignored safely.",
                       conclusion=f"If this action is suspicious and you didn't do such thing, then you can login to {PUBNAME} and add this email address again."
                       )
    return device, email


def accountInactiveAlert(profile: Profile) -> str:
    device, email = False, False
    device = user_device_notify(profile.user, "Account Deactivated",
                       f"This is to inform you that your {PUBNAME} account ({profile.getEmail()}) has been deactivated."
                       )

    email = sendAlertEmail(to=profile.getEmail(), username=profile.getFName(), subject='Account Deactivated',
                   header=f"This is to inform you that your {PUBNAME} account ({profile.getEmail()}) has been deactivated.",
                   footer=f"If you acknowledge this action, then this email can be ignored safely. You can login to {PUBNAME} anytime and re-activate your account.",
                   conclusion=f"If this action is suspicious and you didn't do such thing, then you should head on to {PUBNAME} and login now."
                   )
    return device, email


def accountReactiveAlert(profile: Profile) -> str:
    device, email = False, False
    device = user_device_notify(profile.user, "Account Re-activated",
                       f"This is to inform you that your {PUBNAME} account ({profile.getEmail()}) has been re-activated."
                       )

    email = sendAlertEmail(to=profile.getEmail(), username=profile.getFName(), subject='Account Re-activated',
                   header=f"This is to inform you that your {PUBNAME} account ({profile.getEmail()}) has been re-activated.",
                   footer=f"If you acknowledge this action, then this email can be ignored safely. You can login to {PUBNAME} and deactivate your account anytime.",
                   conclusion=f"If this action is suspicious and you didn't do such thing, then please report to us."
                   )
    return device, email


def accountDeleteAlert(user: User) -> str:
    device, email = False, False
    device = user_device_notify(user, "New Email Address Removed",
                       f"With heavy heart, this is to inform you that your {PUBNAME} account ({user.email}) has been DELETED."
                       )

    email = sendAlertEmail(to=user.email, username=user.first_name, subject='Account Deleted',
                   header=f"With heavy heart, this is to inform you that your {PUBNAME} account ({user.email}) has been DELETED.",
                   footer=f"We're sad to see you go. You can no longer access anything related to your account now, as this action was irreversible.",
                   conclusion=f"If this action is suspicious and you didn't do such thing, then please report to us."
                   )
    return device, email


def successorInvite(successor: User, predecessor: User) -> str:
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=successor, device_notification__notification__code=NotificationCode.SUCCESSOR_INVITE).exists():
        device = user_device_notify(successor, "Profile Successor Invitation",
                           f"{predecessor.getName()} wants you to be their successor on {PUBNAME}, and therefore has invited you by following link button.",
                           predecessor.profile.getSuccessorInviteLink())

    if EmailNotificationSubscriber.objects.filter(user=successor, email_notification__notification__code=NotificationCode.SUCCESSOR_INVITE).exists():
        email = sendActionEmail(to=successor.email, username=successor.first_name, subject='Profile Successor Invitation',
                        header=f"{predecessor.getName()} wants you to be their successor on {PUBNAME}, and therefore has invited you by following link button.",
                        actions=[{
                               'text': 'View succession invitation',
                               'url': predecessor.profile.getSuccessorInviteLink()
                        }],
                        footer=f"Visit the above link to decide whether you'd want to take control of {predecessor.getName()}'s assets whenever they leave {PUBNAME}.",
                        conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
                        )
    return device, email


def successorAccepted(successor: User, predecessor: User) -> str:
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=predecessor, device_notification__notification__code=NotificationCode.SUCCESSOR_ACCEPTED).exists():
        device = user_device_notify(predecessor, "Profile Successor Invitation",
                           f"This is to inform you that {successor.getName()} has accepted to be your successor on {PUBNAME}.",
                           successor.profile.getLink())

    if EmailNotificationSubscriber.objects.filter(user=predecessor, email_notification__notification__code=NotificationCode.SUCCESSOR_ACCEPTED).exists():
        email = sendActionEmail(to=predecessor.email, username=predecessor.first_name, subject='Successor Accepted Invitation',
                        header=f"This is to inform you that {successor.getName()} has accepted to be your successor on {PUBNAME}.",
                        actions=[{
                               'text': 'View successor',
                               'url': successor.profile.getLink()
                        }],
                        footer=f"{successor.getName()} will take control of your assets whenever you leave {PUBNAME} by deleting your account. You can change successor through your account security settings.",
                        conclusion=f"This email was sent because you requested a successor for your {PUBNAME} account. If this wasn't you, then remove the successor in your account security settings."
                        )
    return device, email


def successorDeclined(successor: User, predecessor: User) -> str:
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=predecessor, device_notification__notification__code=NotificationCode.SUCCESSOR_DECLINED).exists():
        device = user_device_notify(predecessor, "Successor Declined Invitation",
                           f"This is to inform you that {successor.getName()} has declined to be your successor on {PUBNAME}.")

    if EmailNotificationSubscriber.objects.filter(user=predecessor, email_notification__notification__code=NotificationCode.SUCCESSOR_DECLINED).exists():
        email = sendAlertEmail(to=predecessor.email, username=predecessor.first_name, subject='Successor Declined Invitation',
                       header=f"This is to inform you that {successor.getName()} has declined to be your successor on {PUBNAME}.",
                       footer=f"You can request another successor using the same way you requested for {successor.getName()}.",
                       conclusion=f"This email was sent because you requested a successor for your {PUBNAME} account. If this wasn't you, then please report to us."
                       )
    return device, email


def assetMigrationProblem(predecessor: User) -> str:
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=predecessor, device_notification__notification__code=NotificationCode.SUCCESSOR_DECLINED).exists():
        device = user_device_notify(predecessor, "Asset Migration Error",
                           "This is to inform you that the migration of your profile assets to the successor was not successful.")

    if EmailNotificationSubscriber.objects.filter(user=predecessor, email_notification__notification__code=NotificationCode.MIGRATION_PROBLEM).exists():
        email = sendActionEmail(to=predecessor.email, username=predecessor.first_name, subject='Asset Migration Error',
                        header="This is to inform you that the migration of your profile assets to the successor was not successful."
                        "This could happen due to many reasons, including:<br/>"
                        "+ The successor you chose has not a valid account, or is no longer a valid user.<br/>"
                        "+ The successor you chose may not be suitable for your assets (difference in type of accounts, etc.)<br/>",
                        actions=[{
                               'text': 'View account settings',
                               'url': f"{url.getRoot(APPNAME)}{url.INDEX}"
                        }],
                        footer="Deletion of your account was halted for the moment. Please visit your account settings and choose a new successor and retry deleting your account. If problem persists, you may contact us.",
                        conclusion=f"This email was sent because your account deletion for {PUBNAME} account encountered problems. If this wasn't you, then please report to us."
                        )
    return device, email


def send_account_verification_email(request: WSGIRequest):
    send_email_confirmation(request, request.user)
    return True
