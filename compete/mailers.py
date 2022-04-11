from main.env import PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail, sendCCActionEmail
from main.strings import URL, url
from people.models import Profile

from .apps import APPNAME
from .models import (AppreciationCertificate, Competition,
                     ParticipantCertificate, Submission)


def participantInviteAlert(profile: Profile, host: Profile, submission: Submission) -> str:
    """
    Email invitation to a user for participation with a submission in a competition.
    """
    return sendActionEmail(
        to=profile.get_email, username=profile.getFName(), subject='Invitation to Participate Together',
        header=f"{host.get_name} ({host.get_email}) has invited you to participate with them in our upcoming competition \'{submission.competition.title}\'.",
        actions=[{'text': "See invitation",
                  'url': f"{url.getRoot(APPNAME)}{URL.compete.invitation(submission.get_id,profile.getUserID())}"}],
        footer=f"You may accept or deny this invitation. If you won't respond, then this invitation will automatically become invalid at the end of competition, or, upon final submission, or, cancellation of your invitation by {host.get_name}, whichever occurrs earlier.",
        conclusion=f"You can ignore this email if you're not interested. If you're being spammed by this invitation or this is an error, please report to us."
    )


def participantWelcomeAlert(profile: Profile, submission: Submission) -> str:
    """
    Email alert to a participant of a submission notifying their participation confirmation
    """
    done = sendActionEmail(
        to=profile.get_email, username=profile.getFName(), subject=f"Your Participation Confirmed",
        header=f"This is to inform you that you've participated in our '{submission.competition.title}' competition. Great! With a lots of goodluck from {PUBNAME} Community, make sure you put your 100% efforts in this.",
        actions=[{'text': "View competition",
                  'url': f'{submission.competition.get_link}'}],
        footer=f"If you have other people with you, actively coordinate with them, and if you don't have a team, invite someone. However, if you are a lone wolf, then the community is always there for you.",
        conclusion=f"You received this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
    )
    if done:
        return participantJoinedAlert(profile, submission)


def participantJoinedAlert(profile: Profile, submission: Submission) -> str:
    """
    Email alert to existing members of a submission notifying confirmed inclusion of a new member.
    """
    emails = submission.getMembersEmail()
    if len(emails) < 2:
        return True
    return sendCCActionEmail(
        to=list(filter(lambda e: e != profile.get_email, emails)),
        subject=f"Teammate Joined Submission",
        header=f"This is to inform you that '{profile.getName()}' has joined your team in '{submission.competition.title}' competition.",
        actions=[{'text': "View competition",
                  'url': f'{submission.competition.get_link}'}],
        footer=f"Someone from your team, or you had invited {profile.getFName()} to join your submission, and they have accepted the invite.",
        conclusion=f"You received this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
    )


def participationWithdrawnAlert(profile: Profile, submission: Submission) -> str:
    """
    Email alert to a participant of a submission notifying their participation cancellation
    """
    return sendActionEmail(
        to=profile.get_email, username=profile.getFName(), subject=f"Your Participation Cancelled",
        header=f"This is to inform you that your existing participation in our '{submission.competition.title}' competition has been cancelled. Either someone has removed you from your team, or you have withdrawn yourself.",
        actions=[{'text': "View competition",
                  'url': f'{submission.competition.get_link}'}],
        footer=f"If you acknowledge this action, then this email can be ignored. You can participate independently again, as long as the competition is active.",
        conclusion=f"You received this email because your participation was cancelled in a competition at {PUBNAME}. If this is unexpected, please report to us."
    )


def submissionConfirmedAlert(submission: Submission) -> list:
    """
    Email alert to all participants of a submission indicating their submission has been submitted successfully.
    """
    return list(map(
        lambda profile: sendAlertEmail(
            to=profile.get_email, username=profile.getFName(), subject=f"Submission Submitted Successfully",
            header=f"This is to inform you that your submission for '{submission.competition.title}' competition was successfully submitted at {submission.submitOn}.{' Your submission was late, and hence is vulnerable to rejection.' if submission.late else ''} Submission ID: {submission.getID()}",
            footer=f"Your submission has been safely kept for review, and the results will be declared for all the submissions we have received, altogether, soon. Till then, chill out. We're lenient.",
            conclusion=f"You received this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
        ), submission.getMembers()
    ))


def submissionsModeratedAlert(competition: Competition) -> list:
    """
    Email alert to manager and all judges of a competition indicating the submissions have been moderated by the moderator.
    """
    if (not competition.moderated()) or competition.resultDeclared:
        return False
    return list(map(
        lambda judge: sendActionEmail(
            to=judge.get_email,
            subject=f"Submissions Judgement Ready: {competition.title}",
            greeting=f"Respected judge",
            username=judge.get_name,
            header=f"The submissions for '{competition.title}' competition have been made ready for judgement by the moderator. You may now proceed with alloting points to submissions.",
            actions=[{
                'text': 'View submissions',
                'url': competition.getJudgementLink(),
            }],
            footer=f"Your assigned points will be the decisive factor for final rankings of submissions, therefore please judge carefully.",
            conclusion=f"You received this email because you are a judge for the mentioned competition. If this is an error, then please report to us."
        ), competition.getJudges()
    ))


def submissionsJudgedAlert(competition: Competition, judge: Profile) -> str:
    """
    Email alert to the manager of a competition indicating the submissions have been judged by the given judge.
    """
    if (not competition.moderated()) or competition.resultDeclared or (not competition.allSubmissionsMarkedByJudge(judge)):
        return False
    return sendActionEmail(
        to=competition.creator.get_email,
        subject=f"Submissions Judged: {competition.title}",
        username=competition.creator.get_name,
        header=f"The submissions for '{competition.title}' competition have been judged by the respected judge - {judge.get_name}. You can check the status of judgment.",
        actions=[{
            'text': 'View competition',
            'url': competition.getManagementLink(),
        }],
        footer=f"You will be able to declare the results, once all judges submit their judgement on all submissions.",
        conclusion=f"You received this email because you are the manager of the mentioned competition. If this is an error, then please report to us."
    )


def resultsDeclaredAlert(competition: Competition) -> list:
    """
    Notify results to everyone involved in given competition
    """
    if not competition.resultDeclared:
        return False
    return [
        sendActionEmail(
            to=competition.creator.get_email,
            subject=f"Results Declared: {competition.title}",
            username=competition.creator.get_name,
            header=f"This is to inform you that the results of '{competition.title}' competition have been declared. You can generate the certificates of all participants at one click only, by visiting the following link.",
            actions=[{
                'text': 'View competition',
                'url': competition.getManagementLink(),
            }],
            footer=f"Do generate the certificates as soon as possible, as every participant is waiting for their certificate.",
            conclusion=f"You received this email because you are the manager of the mentioned competition. If this is an error, then please report to us."
        ),
        resultsDeclaredModeratorAlert(competition),
        resultsDeclaredJudgeAlert(competition),
        resultsDeclaredParticipantAlert(competition)
    ]


def certsAllotedAlert(competition: Competition) -> list:
    """
    Notify certficates allotment to every receiver in given competition
    """
    if not competition.resultDeclared:
        return False
    return [
        sendActionEmail(
            to=competition.creator.get_email,
            subject=f"Certificates Alloted: {competition.title}",
            username=competition.creator.get_name,
            header=f"This is to inform you that the certificates of participants for the '{competition.title}' competition have been alloted successfully.",
            actions=[{
                'text': 'View competition',
                'url': competition.getManagementLink(),
            }],
            footer=f"This marks the successfull end of this competition. Thank you for managing this competition, and thus contributing towards betterment of the {PUBNAME} platform.",
            conclusion=f"You received this email because you are the manager of the mentioned competition. If this is an error, then please report to us."
        ),
        list(map(
            lambda apprcert: sendActionEmail(
                to=apprcert.appreciatee.get_email,
                subject=f"Certificate Available: {competition.title}",
                greeting="Greetings",
                username=apprcert.appreciatee.get_name,
                header=f"Your certficate of appreciation in '{competition.title}' competition has been alloted, and can be accessed permanently via following link.",
                actions=[{
                    'text': 'View certficate',
                    'url': apprcert.get_link
                }],
                footer=f"Your can download your certificate, or just share it from the page itself. Any delay in allotment is deeply regretted. Thank you.",
                conclusion=f"You received this email because you contributed in the mentioned competition. If this is an error, then please report to us."
            ), AppreciationCertificate.objects.filter(competition=competition)
        )),
        list(map(
            lambda partcert: sendActionEmail(
                to=partcert.profile.get_email,
                subject=f"Certificate Available: {competition.title}",
                header=f"Surprise! Your certficate of participation in '{competition.title}' competition has been alloted, and can be accessed permanently via following link.",
                actions=[{
                        'text': 'View certficate',
                        'url': partcert.get_link
                }],
                footer=f"Your can download your certificate, or just share it from the page itself. Any delay in allotment is deeply regretted. Keep participating!",
                conclusion=f"You received this email because you participated the mentioned competition. If this is an error, then please report to us."
            ), ParticipantCertificate.objects.filter(result__competition=competition)
        ))
    ]


def resultsDeclaredParticipantAlert(competition: Competition) -> list:
    """
    Notify results to every participant in given competition
    """
    if not competition.resultDeclared:
        return False
    return list(map(
        lambda sub: sendCCActionEmail(
            to=sub.getMembersEmail(),
            subject=f"Results Declared: {competition.title}",
            header=f"This is to inform you that the results of '{competition.title}' competition have been declared. You may check your submission ranking now, and don't forget to claim your XP!",
            actions=[{
                'text': 'View results',
                'url': f"{competition.get_link}?tab=4"
            }],
            footer=f"The results were based on aggregated markings by independent judgement panel. This marks the successfull end of this competition. Thank you for participating, see you again in upcoming competitions!",
            conclusion=f"You received this email because you participated the mentioned competition. If this is an error, then please report to us."
        ), competition.getValidSubmissions()
    ))


def resultsDeclaredJudgeAlert(competition: Competition) -> list:
    """
    Notify results to every judge in given competition
    """
    if not competition.resultDeclared:
        return False
    return list(map(
        lambda judge: sendActionEmail(
            to=judge.get_email,
            subject=f"Results Declared: {competition.title}",
            greeting=f"Respected judge",
            username=judge.get_name,
            header=f"This is to inform you that the results of '{competition.title}' competition have been declared. This marks the successfull end of this competition. The following link button will lead you to competition results page.",
            actions=[{
                'text': 'View results',
                'url': f"{competition.get_link}?tab=4"
            }],
            footer=f"The results were based on aggregated markings by independent judgement panel, including you. It was an honour to have you as judge for this competition.",
            conclusion=f"You received this email because you judged the mentioned competition. If this is an error, then please report to us."
        ), competition.getJudges()
    ))


def resultsDeclaredModeratorAlert(competition: Competition) -> str:
    """
    Notify results to the moderator in given competition
    """
    if not competition.resultDeclared:
        return False
    mod = competition.getModerator()
    return sendActionEmail(
        to=mod.get_email,
        username=mod.get_name,
        subject=f"Results Declared: {competition.title}",
        header=f"This is to inform you that the results of '{competition.title}' competition have been declared. This marks the successfull end of the competition.",
        actions=[{
            'text': 'View results',
            'url': f"{competition.get_link}?tab=4"
        }],
        footer=f"The results were based on aggregated markings by independent judgement panel. All participants will be informed shortly. Thank you for ensuring successfull conduction of this competition.",
        conclusion=f"You received this email because you moderated the mentioned competition. If this is an error, then please report to us."
    )
