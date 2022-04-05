from main.env import BOTMAIL, PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail, sendEmail
from people.models import Profile

from management.models import ContactRequest, Management, ManagementInvitation


def alertLegalUpdate(docname, docurl):
    emails = Profile.objects.filter(
        is_active=True, to_be_zombie=False).values_list('user__email', flat=True)
    for email in emails:
        sendActionEmail(
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
    # print(f"{emails.count()} people alerted for change in {docname}")
    return True


def managementInvitationSent(invite: ManagementInvitation):
    """
    Invitation to accept project ownership
    """
    if invite.resolved:
        return False
    if invite.expired:
        return False
    return sendActionEmail(
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


def managementInvitationAccepted(invite: ManagementInvitation):
    """
    Invitation to accept project ownership
    """
    if not invite.resolved:
        return False

    return sendActionEmail(
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


def managementPersonRemoved(mgm: Management, person: Profile):
    """
    Remvoing a member from an organization alert
    """
    return sendAlertEmail(
        to=person.getEmail(),
        username=person.getFName(),
        subject=f"Organization Membership Terminated",
        header=f"You've been detached from {mgm.get_name} organization at {PUBNAME}.",
        footer=f"Either this was your action, or the manager itself. Contact them if there's a mistake.",
        conclusion=f"This email was sent because your membership has been terminated from the organization in Knotters."
    )


def newContactRequestAlert(contactRequest: ContactRequest):
    return sendEmail(
        to=BOTMAIL,
        subject="New Contact Request",
        body=f"New contact request from {contactRequest.senderName} ({contactRequest.senderEmail}) on {contactRequest.createdOn}.\n\nCategory: {contactRequest.contactCategory.name}\n\nRequest Message: {contactRequest.message}\n",
        html=f"New contact request from {contactRequest.senderName} ({contactRequest.senderEmail}) on {contactRequest.createdOn}.\n\nCategory: {contactRequest.contactCategory.name}\n\nRequest Message: {contactRequest.message}\n"
    )
