from main.mailers import sendAlertEmail, sendActionEmail
from allauth.account.utils import send_email_confirmation
from allauth.account.models import EmailAddress
from main.env import PUBNAME
from people.models import User, Profile


def passordChangeAlert(user: User) -> bool:
    return sendAlertEmail(to=user.email, username=user.first_name, subject='Account Password Changed',
                          header=f"This is to inform you that your {PUBNAME} account ({user.email}) password was changed recently.",
                          footer="If you acknowledge this action, then this email can be ignored safely.",
                          conclusion=f"If this action is suspicious and you didn't do such thing, then immediately head on to {PUBNAME} and request a password reset by choosing 'forgot' on login."
                          )


def emailUpdateAlert(user: User, oldEmail: str, newEmail: str) -> bool:
    if EmailAddress.objects.filter(user=user, verified=True).exists():
        return sendAlertEmail(to=oldEmail, username=user.first_name, subject='Primary Email Address Changed',
                            header=f"This is to inform you that your {PUBNAME} primary email address was changed from {oldEmail} to {newEmail}, recently.",
                            footer="If you acknowledge this action, then this email can be ignored safely.",
                            conclusion=f"If this action is suspicious and you didn't do such thing, then please report to us. Your {PUBNAME} account may have been compromised."
                            )


def emailAddAlert(user: User, newEmail: str) -> bool:
    if EmailAddress.objects.filter(user=user, verified=True).exists():
        return sendAlertEmail(to=user.email, username=user.first_name, subject='New Email Address Added',
                            header=f"This is to inform you that a new email address ({newEmail}) was added to your {PUBNAME} account, recently. This however, will NOT affect your existing ({user.email}) login email address.",
                            footer="If you acknowledge this action, then this email can be ignored safely.",
                            conclusion=f"If this action is suspicious and you didn't do such thing, then immediately login to {PUBNAME} and remove this new email address from your acccount."
                            )


def emailRemoveAlert(user: User, removedEmail: str) -> bool:
    if EmailAddress.objects.filter(user=user, verified=True).exists():
        return sendAlertEmail(to=user.email, username=user.first_name, subject='Email Address Removed',
                            header=f"This is to inform you that an email address ({removedEmail}) was removed from your {PUBNAME} account.",
                            footer="If you acknowledge this action, then this email can be ignored safely.",
                            conclusion=f"If this action is suspicious and you didn't do such thing, then you can login to {PUBNAME} and add this email address again."
                            )


def accountInactiveAlert(profile: Profile) -> bool:
    return sendAlertEmail(to=profile.getEmail(), username=profile.getFName(), subject='Account Deactivated',
                          header=f"This is to inform you that your {PUBNAME} account ({profile.getEmail()}) has been deactivated.",
                          footer=f"If you acknowledge this action, then this email can be ignored safely. You can login to {PUBNAME} anytime and re-activate your account.",
                          conclusion=f"If this action is suspicious and you didn't do such thing, then you should head on to {PUBNAME} and login now."
                          )


def accountReactiveAlert(profile: Profile) -> bool:
    return sendAlertEmail(to=profile.getEmail(), username=profile.getFName(), subject='Account Re-activated',
                          header=f"This is to inform you that your {PUBNAME} account ({profile.getEmail()}) has been re-activated.",
                          footer=f"If you acknowledge this action, then this email can be ignored safely. You can login to {PUBNAME} and deactivate your account anytime.",
                          conclusion=f"If this action is suspicious and you didn't do such thing, then please report to us."
                          )


def accountDeleteAlert(user: User) -> bool:
    return sendAlertEmail(to=user.email, username=user.first_name, subject='Account Deleted',
                        header=f"With heavy heart, this is to inform you that your {PUBNAME} account ({user.email}) has been DELETED.",
                        footer=f"We're sad to see you go. You can no longer access anything related to your account now, as this action was irreversible.",
                        conclusion=f"If this action is suspicious and you didn't do such thing, then please report to us."
                        )


def successorInvite(successor: User, predecessor: User) -> bool:
    return sendActionEmail(to=successor.email, username=successor.first_name, subject='Profile Successor Invitation',
                           header=f"{predecessor.getName()} wants you to be their successor on {PUBNAME}, and therefore has invited you by following link button.",
                           actions=[{
                               'text': 'View succession invitation',
                               'url': predecessor.profile.getSuccessorInviteLink()
                           }],
                           footer=f"Visit the above link to decide whether you'd want to take control of {predecessor.getName()}'s assets whenever they leave {PUBNAME}.",
                           conclusion=f"Nothing will happen by merely visiting the above link. We recommed you to visit the link and make you decision there."
                           )


def successorAccepted(successor: User, predecessor: User) -> bool:
    return sendActionEmail(to=predecessor.email, username=predecessor.first_name, subject='Successor Accepted Invitation',
                           header=f"This is to inform you that {successor.getName()} has accepted to be your successor on {PUBNAME}.",
                           actions=[{
                               'text': 'View successor',
                               'url': successor.profile.getLink()
                           }],
                           footer=f"{successor.getName()} will take control of your assets whenever you leave {PUBNAME} by deleting your account. You can change successor through your account security settings.",
                           conclusion=f"This email was sent because you requested a successor for your {PUBNAME} account. If this wasn't you, then remove the successor in your account security settings."
                           )


def successorDeclined(successor: User, predecessor: User) -> bool:
    return sendAlertEmail(to=predecessor.email, username=predecessor.first_name, subject='Successor Declined Invitation',
                          header=f"This is to inform you that {successor.getName()} has declined to be your successor on {PUBNAME}.",
                          footer=f"You can request another successor using the same way you requested for {successor.getName()}.",
                          conclusion=f"This email was sent because you requested a successor for your {PUBNAME} account. If this wasn't you, then please report to us."
                          )

def send_account_verification_email(request):
    send_email_confirmation(request, request.user)
    return True