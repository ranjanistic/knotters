from allauth.account.models import EmailAddress
from main.env import PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail, sendToAdmin
from people.models import Profile
from auth2.models import DeviceNotificationSubscriber, EmailNotificationSubscriber
from management.models import ContactRequest, Management, ManagementInvitation
from main.constants import NotificationCode
from main.methods import user_device_notify


def alertLegalUpdate(docname: str, docurl: str) -> list:
    """

    Args:
        docname (str): Name of the document
        docurl (str): URL of the document

    Returns:
        list<list>: List of emails and corresponding queue task IDs
    """
    emails = EmailAddress.objects.filter(
        primary=True, verified=True).values_list("email", flat=True)
    done = []
    for email in emails:
        if DeviceNotificationSubscriber.objects.filter(user=email, device_notification__notification__code=NotificationCode.ALERT_LEGAL_UPDATE).exists():
            device = user_device_notify(email, f"Update to our {docname}",
                               f"This is to infom you that our {docname} document was updated recently. You can read the latest information anytime from the following link", docurl)
        if EmailNotificationSubscriber.objects.filter(user=email, email_notification__notification__code=NotificationCode.ALERT_LEGAL_UPDATE).exists():
            email = sendActionEmail(
                to=email,
                subject=f"Update to our {docname}",
                header=f"This is to infom you that our {docname} document was updated recently. You can read the latest information anytime from the following link",
                actions=[dict(
                    text=f'View updated {docname}',
                    url=docurl
                )],
                footer="It is our duty to keep you updated with changes in our terms & policies.",
                conclusion=f"This email was sent because we have updated a legal document from our side, which may concern you as you are a member at {PUBNAME}."
            )
        done.append([device, email])
    return done


def managementInvitationSent(invite: ManagementInvitation) -> str:
    """To send invitation to a new member in an organization
    Args:
        invite (ManagementInvitation): Invitation instance

    Returns:
        str: Task ID of the email
    """
    if invite.resolved:
        return False
    if invite.expired:
        return False
    user_device_notify(invite.receiver.user, f"Organization Invitation",
                       f"You've been invited to be a member of {invite.management.get_name} at {PUBNAME}.", invite.get_link)
    sendActionEmail(
        to=invite.receiver.getEmail(),
        username=invite.receiver.getFName(),
        subject=f"Organization Invitation",
        header=f"You've been invited to be a member of {invite.management.get_name} at {PUBNAME}.",
        actions=[{
                'text': 'View Invitation',
                'url': invite.get_link
        }],
        footer=f"Visit the above link to decide whether you'd like to join the organization at {PUBNAME}.",
        conclusion=f"We recommed you to visit the link and make you decision there. You can block the user if this is a spam."
    )


def managementInvitationAccepted(invite: ManagementInvitation) -> str:
    """To send email to the user who accepted the invitation

    Args:
        invite (ManagementInvitation): Invitation instance

    Returns:
        str: Task ID of the email
    """
    if not invite.resolved:
        return False
    if DeviceNotificationSubscriber.objects.filter(user=invite.receiver.user, device_notification__notification__code=NotificationCode.MANAGEMENT_INVITATION_ACCEPTED).exists():
        user_device_notify(invite.receiver.user, f"Organization Invitation Accepted",
                           f"You've accepted the membership of {invite.management.get_name} organization at {PUBNAME}.", invite.management.get_link)
    if EmailNotificationSubscriber.objects.filter(user=invite.receiver.user, email_notification__notification__code=NotificationCode.MANAGEMENT_INVITATION_ACCEPTED).exists():
        sendActionEmail(
            to=invite.receiver.getEmail(),
            username=invite.receiver.getFName(),
            subject=f"Organization Invitation Accepted",
            header=f"You've accepted the membership of {invite.management.get_name} organization at {PUBNAME}.",
            actions=[{
                'text': 'View organization',
                'url': invite.management.get_link
            }],
            footer=f"Now you'll get collective growth and perks from your organization on {PUBNAME}, among other benefits.",
            conclusion=f"This email was sent because you accepted an organization's membership invitation."
        )


def managementPersonRemoved(mgm: Management, person: Profile) -> str:
    """To send email to the user who was removed from an organization

    Args:
        mgm (Management): Management instance
        person (Profile): Profile instance of removed member

    Returns:
        str: Task ID of the email
    """

    user_device_notify(person.user, f"Organization Membership Terminated",
                       f"You've been detached from {mgm.get_name} organization at {PUBNAME}.")

    sendAlertEmail(
        to=person.getEmail(),
        username=person.getFName(),
        subject=f"Organization Membership Terminated",
        header=f"You've been detached from {mgm.get_name} organization at {PUBNAME}.",
        footer=f"Either this was your action, or the manager itself. Contact them if there's a mistake.",
        conclusion=f"This email was sent because your membership has been terminated from the organization in Knotters."
    )


def newContactRequestAlert(contactRequest: ContactRequest) -> str:
    """To send email to admin for a new contact request

    Args:
        contactRequest (ContactRequest): ContactRequest instance

    Returns:
        str: Task ID of the email
    """
    return sendToAdmin(
        subject="New Contact Request",
        body=f"New contact request from {contactRequest.senderName} ({contactRequest.senderEmail}) on {contactRequest.createdOn}.\n\nCategory: {contactRequest.contactCategory.name}\n\nRequest Message: {contactRequest.message}\n",
        html=f"New contact request from {contactRequest.senderName} ({contactRequest.senderEmail}) on {contactRequest.createdOn}.<br/><br/>Category: {contactRequest.contactCategory.name}<br/><br/>Request Message: {contactRequest.message}\n"
    )
