from main.methods import sendActionEmail, sendAlertEmail
from main.env import SITE
from people.models import Profile
from .models import Submission
from .apps import APPNAME

def sendParticipantInvitationMail(profile: Profile, host: Profile, submission: Submission) -> bool:
    """
    Email invitation to a user for participation with a submission in a competition.
    """
    return sendActionEmail(
        to=profile.user.email, username=profile.user.first_name, subject='Invitation to Participate Together',
        header=f"{host.user.getName()} ({host.user.email}) has invited you to participate with them in our upcoming competition \'{submission.competition.title}\'.",
        actions=[{'text': "See invitation",
                  'url': f'{SITE}/{APPNAME}/invitation/{submission.id}/{profile.user.id}'}],
        footer=f"You may accept or deny this invitation. If you won't respond, then this invitation will automatically become invalid at the end of competition, or, upon final submission or cancellation of your invitation by {host.user.getName()}, whichever occurrs earlier.",
        conclusion=f"You can ignore this email if you're not interested. If you're being spammed by this invitation, please report to us by replying to this email."
    )


def sendParticipationWelcomeMail(profile: Profile, submission: Submission) -> bool:
    """
    Email alert to a participants of a submission notifying their participation confirmation
    """
    return sendActionEmail(
        to=profile.user.email, username=profile.user.first_name, subject=f"Your Participation Confirmed",
        header=f"This is to inform you that you've participated in our '{submission.competition.title}' competition. Great! With a lots of goodluck from Knotters Community, make sure you put your 100% efforts in this.",
        actions=[{'text': "View competition",
                  'url': f'{SITE}/{submission.competition.getLink()}'}],
        footer=f"If you have other people with you, actively coordinate with them, and if you don't have a team, invite someone. However, if you are a lone wolf, then the community is always there for you.",
        conclusion=f"You recieved this email because you participated in a competition at Knotters. If this is unexpected, please report to us by replying to this email."
    )


def sendSubmissionConfirmedMail(profiles: list, submission: Submission) -> bool:
    """
    Email alert to all participants of a submission indicating their submission has been submitted successfully.
    """
    for profile in profiles:
        sendAlertEmail(
            to=profile.user.email, username=profile.user.first_name, subject=f"Submission Submitted Successfully",
            header=f"This is to inform you that your submission of participation in '{submission.competition.title}' competition was successfully submitted at {submission.submitOn} (IST Asia/Kolkata).{' Your submission was late.' if submission.late else ''}. Submission ID: {submission.id}",
            footer=f"Your submission has been safely kept for review, and the results will be declared for all the submissions we have recieved, altogether, soon. Till then, chill out! NOTE: We're lenient.",
            conclusion=f"You recieved this email because you participated in a competition at Knotters. If this is unexpected, please report to us by replying to this email."
        )
