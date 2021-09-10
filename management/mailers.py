from people.models import Profile
from main.env import PUBNAME
from main.mailers import sendActionEmail

def alertLegalUpdate(docname, docurl):
    emails = Profile.objects.filter(is_active=True,to_be_zombie=False).values_list('user__email',flat=True)
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
    print(f"{emails.count()} people alerted for change in {docname}")

