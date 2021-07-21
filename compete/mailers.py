from main.mailers import sendActionEmail, sendAlertEmail, sendCCActionEmail
from main.env import PUBNAME
from people.models import Profile
from .models import Competition, Submission
from .apps import APPNAME


def participantInviteAlert(profile: Profile, host: Profile, submission: Submission) -> bool:
    """
    Email invitation to a user for participation with a submission in a competition.
    """
    return sendActionEmail(
        to=profile.getEmail(), username=profile.getFName(), subject='Invitation to Participate Together',
        header=f"{host.getName()} ({host.getEmail()}) has invited you to participate with them in our upcoming competition \'{submission.competition.title}\'.",
        actions=[{'text': "See invitation",
                  'url': f'{APPNAME}/invitation/{submission.getID()}/{profile.getUserID()}'}],
        footer=f"You may accept or deny this invitation. If you won't respond, then this invitation will automatically become invalid at the end of competition, or, upon final submission, or, cancellation of your invitation by {host.getName()}, whichever occurrs earlier.",
        conclusion=f"You can ignore this email if you're not interested. If you're being spammed by this invitation or this is an error, please report to us."
    )


def participantWelcomeAlert(profile: Profile, submission: Submission) -> bool:
    """
    Email alert to a participant of a submission notifying their participation confirmation
    """
    sendActionEmail(
        to=profile.getEmail(), username=profile.getFName(), subject=f"Your Participation Confirmed",
        header=f"This is to inform you that you've participated in our '{submission.competition.title}' competition. Great! With a lots of goodluck from {PUBNAME} Community, make sure you put your 100% efforts in this.",
        actions=[{'text': "View competition",
                  'url': f'{submission.competition.getLink()}'}],
        footer=f"If you have other people with you, actively coordinate with them, and if you don't have a team, invite someone. However, if you are a lone wolf, then the community is always there for you.",
        conclusion=f"You recieved this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
    )
    return participantJoinedAlert(profile,submission)

def participantJoinedAlert(profile:Profile,submission:Submission) -> bool:
    """
    Email alert to existing members of a submission notifying confirmed inclusion of a new member.
    """
    emails = submission.getMembersEmail()
    if len(emails) < 2: return True 
    finalEmails = []
    for email in emails:
        if email != profile.getEmail():
            finalEmails.append(email)
    return sendCCActionEmail(
        to=finalEmails,
        subject=f"Teammate Joined Submission",
        greeting="Hello participant",
        header=f"This is to inform you that '{profile.getName()}' has joined your team in '{submission.competition.title}' competition.",
        actions=[{'text': "View competition",
                'url': f'{submission.competition.getLink()}'}],
        footer=f"Someone from your team, or you had invited {profile.getFName()} to join your submission, and they have accepted the invite.",
        conclusion=f"You recieved this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
    )

def participationWithdrawnAlert(profile: Profile, submission: Submission) -> bool:
    return sendActionEmail(
        to=profile.getEmail(), username=profile.getFName(), subject=f"Your Participation Cancelled",
        header=f"This is to inform you that your existing participation in our '{submission.competition.title}' competition has been cancelled. Either someone has removed you from your team, or you have withdrawn yourself.",
        actions=[{'text': "View competition",
                  'url': f'{submission.competition.getLink()}'}],
        footer=f"If you acknowledge this action, then this email can be ignored. You can participate independently again, as long as the competition is active.",
        conclusion=f"You recieved this email because your participation was cancelled in a competition at {PUBNAME}. If this is unexpected, please report to us."
    )


def submissionConfirmedAlert(submission: Submission) -> bool:
    """
    Email alert to all participants of a submission indicating their submission has been submitted successfully.
    """
    profiles = submission.getMembers()
    for profile in profiles:
        sendAlertEmail(
            to=profile.getEmail(), username=profile.getFName(), subject=f"Submission Submitted Successfully",
            header=f"This is to inform you that your submission for '{submission.competition.title}' competition was successfully submitted at {submission.submitOn} (IST, Asia/Kolkata).{' Your submission was late.' if submission.late else ''}. Submission ID: {submission.getID()}",
            footer=f"Your submission has been safely kept for review, and the results will be declared for all the submissions we have recieved, altogether, soon. Till then, chill out! NOTE: We're lenient.",
            conclusion=f"You recieved this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
        )


def resultsDeclaredAlert(competition: Competition):
    """
    Notify results to everyone involved in given competition
    """
    if not competition.resultDeclared:
        return False
    resultsDeclaredModeratorAlert(competition)
    resultsDeclaredJudgeAlert(competition)
    resultsDeclaredParticipantAlert(competition)


def resultsDeclaredParticipantAlert(competition: Competition):
    if not competition.resultDeclared:
        return False
    subs = competition.getValidSubmissions()
    done = []
    for sub in subs:
        done.append(sendCCActionEmail(
            to=sub.getMembersEmail(),
            subject=f"Results Declared: {competition.title}",
            greeting="Greetings participant!",
            header=f"This is to inform you that the results of '{competition.title}' competition have been decalred. You may check your submission rankings now.",
            actions=[{
                'text': 'View results',
                'url': competition.getLink()
            }],
            footer=f"The results were based on aggregated markings by independent judgement panel. This marks the successfull end of this competition. Thank you for participating. See you in upcoming competitions!",
            conclusion=f"You recieved this email because you participated the mentioned competition. If this is an error, then please report to us."
        ))
    return False not in done


def resultsDeclaredJudgeAlert(competition: Competition):
    if not competition.resultDeclared:
        return False
    judges = competition.getJudges()
    done = []
    for judge in judges:
        done.append(sendActionEmail(
            to=judge.getEmail(),
            subject=f"Results Declared: {competition.title}",
            greeting=f"Respected Judge {judge.getFName()}",
            header=f"This is to inform you that the results of '{competition.title}' competition have been decalred. This marks the successfull end of this competition. The following link button will lead you to competition results page.",
            actions=[{
                'text': 'View results',
                'url': competition.getLink()
            }],
            footer=f"The results were based on aggregated markings by independent judgement panel, including you. It was an honour to have you as judge for this competition.",
            conclusion=f"You recieved this email because you judged the mentioned competition. If this is an error, then please report to us."
        ))
    return False not in done


def resultsDeclaredModeratorAlert(competition: Competition):
    if not competition.resultDeclared:
        return False
    mod = competition.getModerator()
    return sendActionEmail(
        to=mod.user.email,
        username=mod.user.first_name,
        subject=f"Results Declared: {competition.title}",
        header=f"This is to inform you that the results of '{competition.title}' competition have been decalred. This marks the successfull end of the competition.",
        actions=[{
            'text': 'View results',
            'url': competition.getLink()
        }],
        footer=f"The results were based on aggregated markings by independent judgement panel. All participants will be informed shortly. Thank you for ensuring successfull conduction of this competition.",
        conclusion=f"You recieved this email because you moderated the mentioned competition. If this is an error, then please report to us."
    )
