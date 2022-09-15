from auth2.models import DeviceNotificationSubscriber, EmailNotificationSubscriber, Notification
from main.constants import NotificationCode
from main.env import PUBNAME
from main.mailers import sendActionEmail, sendAlertEmail, sendCCActionEmail
from main.methods import user_device_notify
from main.strings import URL, url
from people.models import Profile

from .apps import APPNAME
from .models import (AppreciationCertificate, Competition,
                     ParticipantCertificate, Submission)


def participantInviteAlert(profile: Profile, host: Profile, submission: Submission) -> str:
    """
    Email invitation to a user for participation with a submission in a competition.
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.PART_INVITE_ALERT).exists():
        device = user_device_notify(profile.user, "Participation Invite",
                           f"{host.get_name} ({host.get_email}) has invited you to participate with them in our upcoming competition \'{submission.competition.title}\'.", f"{url.getRoot(APPNAME)}{URL.compete.invitation(submission.get_id,profile.getUserID())}")
    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.PART_INVITE_ALERT).exists():
        email = sendActionEmail(
            to=profile.get_email, username=profile.getFName(), subject='Invitation to Participate Together',
            header=f"{host.get_name} ({host.get_email}) has invited you to participate with them in our upcoming competition \'{submission.competition.title}\'.",
            actions=[{'text': "See invitation",
                      'url': f"{url.getRoot(APPNAME)}{URL.compete.invitation(submission.get_id,profile.getUserID())}"}],
            footer=f"You may accept or deny this invitation. If you won't respond, then this invitation will automatically become invalid at the end of competition, or, upon final submission, or, cancellation of your invitation by {host.get_name}, whichever occurrs earlier.",
            conclusion=f"You can ignore this email if you're not interested. If you're being spammed by this invitation or this is an error, please report to us."
        )
    return device, email


def participantWelcomeAlert(profile: Profile, submission: Submission) -> str:
    """
    Email alert to a participant of a submission notifying their participation confirmation
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.PART_WELCOME_ALERT).exists():
        device = user_device_notify(profile.user, "Participation Confirmed",
                           f"This is to inform you that you've participated in our '{submission.competition.title}' competition. Great! With a lots of goodluck from {PUBNAME} Community, make sure you put your 100% efforts in this.", submission.competition.get_link)

    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.PART_WELCOME_ALERT).exists():
        email = sendActionEmail(
            to=profile.get_email, username=profile.getFName(), subject=f"Your Participation Confirmed",
            header=f"This is to inform you that you've participated in our '{submission.competition.title}' competition. Great! With a lots of goodluck from {PUBNAME} Community, make sure you put your 100% efforts in this.",
            actions=[{'text': "View competition",
                      'url': f'{submission.competition.get_link}'}],
            footer=f"If you have other people with you, actively coordinate with them, and if you don't have a team, invite someone. However, if you are a lone wolf, then the community is always there for you.",
            conclusion=f"You received this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
        )
    participantJoinedAlert(profile, submission)
    return device, email


def participantJoinedAlert(profile: Profile, submission: Submission) -> str:
    """
    Email alert to existing members of a submission notifying confirmed inclusion of a new member.
    """
    profiles = list(filter(lambda e: e != profile, submission.getMembers()))
    if len(profiles) < 1:
        return True
    for members in profiles:
        if DeviceNotificationSubscriber.objects.filter(user=members.user, device_notification__notification__code=NotificationCode.PART_JOINED_ALERT).exists():
            device = user_device_notify(members.user, "Teammate Joined Submission",
                               f"This is to inform you that '{profile.getName()}' has joined your team in '{submission.competition.title}' competition.", submission.competition.get_link)
        if EmailNotificationSubscriber.objects.filter(user=members.user, email_notification__notification__code=NotificationCode.PART_JOINED_ALERT).exists():
            email = sendActionEmail(
                to=members.get_email,
                username=members.getFName(),
                subject=f"Teammate Joined Submission",
                header=f"This is to inform you that '{profile.getName()}' has joined your team in '{submission.competition.title}' competition.",
                actions=[{'text': "View competition",
                          'url': f'{submission.competition.get_link}'}],
                footer=f"Someone from your team, or you had invited {profile.getFName()} to join your submission, and they have accepted the invite.",
                conclusion=f"You received this ema]'//il because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
            )


def participationWithdrawnAlert(profile: Profile, submission: Submission) -> str:
    """
    Email alert to a participant of a submission notifying their participation cancellation
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.PART_WITHDRAWN_ALERT).exists():
        device = user_device_notify(profile.user, "Participation Withdrawn",
                           f"This is to inform you that your existing participation in our '{submission.competition.title}' competition has been cancelled. Either someone has removed you from your team, or you have withdrawn yourself.", submission.competition.get_link)

    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.PART_WITHDRAWN_ALERT).exists():
        email = sendActionEmail(
            to=profile.get_email, username=profile.getFName(), subject=f"Your Participation Cancelled",
            header=f"This is to inform you that your existing participation in our '{submission.competition.title}' competition has been cancelled. Either someone has removed you from your team, or you have withdrawn yourself.",
            actions=[{'text': "View competition",
                      'url': f'{submission.competition.get_link}'}],
            footer=f"If you acknowledge this action, then this email can be ignored. You can participate independently again, as long as the competition is active.",
            conclusion=f"You received this email because your participation was cancelled in a competition at {PUBNAME}. If this is unexpected, please report to us."
        )
    return device, email


def submissionConfirmedAlert(submission: Submission) -> list:
    """
    Email alert to all participants of a submission indicating their submission has been submitted successfully.
    """
    list(map(
        lambda profile: user_device_notify(profile.user, "Submission Submitted Successfully",
                                           f"This is to inform you that your submission for '{submission.competition.title}' competition was successfully submitted at {submission.submitOn}.{' Your submission was late, and hence is vulnerable to rejection.' if submission.late else ''} Submission ID: {submission.getID()}", submission.competition.get_link)
        if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.SUBM_CONFIRM_ALERT).exists() else None, submission.getMembers()))
    return list(map(
        lambda profile: sendAlertEmail(
            to=profile.get_email,
            username=profile.getFName(),
                subject=f"Submission Submitted Successfully",
                header=f"This is to inform you that your submission for '{submission.competition.title}' competition was successfully submitted at {submission.submitOn}.{' Your submission was late, and hence is vulnerable to rejection.' if submission.late else ''} Submission ID: {submission.getID()}",
                footer=f"Your submission has been safely kept for review, and the results will be declared for all the submissions we have received, altogether, soon. Till then, chill out. We're lenient.",
                conclusion=f"You received this email because you participated in a competition at {PUBNAME}. If this is unexpected, please report to us."
                )if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.SUBM_CONFIRM_ALERT).exists() else None, submission.getMembers()))


def submissionsModeratedAlert(competition: Competition) -> list:
    """
    Email alert to manager and all judges of a competition indicating the submissions have been moderated by the moderator.
    """
    if (not competition.moderated()) or competition.resultDeclared:
        return False
    list(map(
        lambda judge: user_device_notify(competition.judge.user, "Submissions Moderated",
                                         f"The submissions for '{competition.title}' competition have been made ready for judgement by the moderator. You may now proceed with alloting points to submissions.", competition.getJudgementLink())
        if DeviceNotificationSubscriber.objects.filter(user=competition.judge.user, device_notification__notification__code=NotificationCode.SUBM_MOD_ALERT).exists() else None, competition.getJudges()))
    return list(map(
        lambda judge: sendActionEmail(
                to=competition.judge.get_email(),
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
                )
        if EmailNotificationSubscriber.objects.filter(user=competition.judge.user, email_notification__notification__code=NotificationCode.SUBM_MOD_ALERT).exists() else None, competition.getJudges()
    ))


def submissionsJudgedAlert(competition: Competition, judge: Profile) -> str:
    """
    Email alert to the manager of a competition indicating the submissions have been judged by the given judge.
    """
    device, email = False, False
    if (not competition.moderated()) or competition.resultDeclared or (not competition.allSubmissionsMarkedByJudge(judge)):
        return False
    if DeviceNotificationSubscriber.objects.filter(user=judge.user, device_notification__notification__code=NotificationCode.SUB_JUDGE_ALERT).exists():
        device = user_device_notify(competition.creator.user, "Submissions Judged",
                           f"The submissions for '{competition.title}' competition have been judged by the respected judge - {judge.get_name}. You can check the status of judgment.", competition.getManagementLink())

    if EmailNotificationSubscriber.objects.filter(user=competition.creator.user, email_notification__notification__code=NotificationCode.SUB_JUDGE_ALERT).exists():
        email = sendActionEmail(
            to=competition.creator.get_email(),
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
    return device, email


def resultsDeclaredAlert(competition: Competition) -> list:
    """
    Notify results to everyone involved in given competition
    """
    device, email = False, False
    if not competition.resultDeclared:
        return False
    if DeviceNotificationSubscriber.objects.filter(user=competition.creator.user, device_notification__notification__code=NotificationCode.RES_DEC_ALERT).exists():
        device = user_device_notify(competition.creator.user, "Results Declared",
                           f"This is to inform you that the results of '{competition.title}' competition have been declared. You can generate the certificates of all participants at one click only, by visiting the following link.", competition.getManagementLink())
    if EmailNotificationSubscriber.objects.filter(user=competition.creator.user, email_notification__notification__code=NotificationCode.RES_DEC_ALERT).exists():
        email = sendActionEmail(
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
        )
    resultsDeclaredModeratorAlert(competition),
    resultsDeclaredJudgeAlert(competition),
    resultsDeclaredParticipantAlert(competition)
    return device, email


def certsAllotedAlert(competition: Competition) -> list:
    """
    Notify certficates allotment to every receiver in given competition
    """
    if not competition.resultDeclared:
        return False
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=competition.creator.user, device_notification__notification__code=NotificationCode.CERT_ALLOT_ALERT).exists():
        device = user_device_notify(competition.creator.user, "Certificates Alloted",
                           f"This is to inform you that the certificates of participants for the '{competition.title}' competition have been alloted successfully.", competition.getManagementLink())

    list(map(
        lambda apprcert: user_device_notify(apprcert.appreciatee.user, "Certificates Alloted",
                                            f"This is to inform you that the certificates of participants for the '{competition.title}' competition have been alloted successfully.", apprcert.get_link)
        if DeviceNotificationSubscriber.objects.filter(apprcert.appreciatee.user, device_notification__notification__code=NotificationCode.CERT_ALLOT_ALERT).exists() else None, AppreciationCertificate.objects.filter(competition=competition)))
    list(map(
        lambda partcert: user_device_notify(partcert.profile.user, f"Certificate Available: {competition.title}",
                                            f"Surprise! Your certficate of participation in '{competition.title}' competition has been alloted, and can be accessed permanently via following link.", partcert.get_link)
        if DeviceNotificationSubscriber.objects.filter(partcert.profile.user, device_notification__notification__code=NotificationCode.CERT_ALLOT_ALERT).exists() else None, ParticipantCertificate.objects.filter(result__competition=competition)))

    if EmailNotificationSubscriber.objects.filter(user=competition.creator.user, email_notification__notification__code=NotificationCode.CERT_ALLOT_ALERT).exists():
        email = sendActionEmail(
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
        )
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
        )if EmailNotificationSubscriber.objects.filter(user=apprcert.appreciatee.user, email_notification__notification__code=NotificationCode.CERT_ALLOT_ALERT).exists() else None, AppreciationCertificate.objects.filter(competition=competition)
    ))
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
        )if EmailNotificationSubscriber.objects.filter(user=partcert.profile.user, email_notification__notification__code=NotificationCode.CERT_ALLOT_ALERT).exists() else None, ParticipantCertificate.objects.filter(result__competition=competition)
    ))
    return device, email


def filteredMails(s: Submission, competition: Competition):
    profiles = list(filter(lambda m: EmailNotificationSubscriber.objects.filter(
        user=m.user, device_notification__notification__code=NotificationCode.PART_JOINED_ALERT).exists(), s.getMembers()))
    emails = list(map(lambda x: x.get_email, profiles))
    if len(emails) < 1:
        return None
    sendCCActionEmail(
        to=emails,
        subject=f"Results Declared: {competition.title}",
        header=f"This is to inform you that the results of '{competition.title}' competition have been declared. You may check your submission ranking now, and don't forget to claim your XP!",
        actions=[{
            'text': 'View results',
            'url': f"{competition.get_link}?tab=4"
        }],
        footer=f"The results were based on aggregated markings by independent judgement panel. This marks the successfull end of this competition. Thank you for participating, see you again in upcoming competitions!",
        conclusion=f"You received this email because you participated the mentioned competition. If this is an error, then please report to us."
    )


def filteredUsers(s: Submission, competition: Competition):
    profiles = list(filter(lambda m: DeviceNotificationSubscriber.objects.filter(
        user=m.user, device_notification__notification__code=NotificationCode.PART_JOINED_ALERT).exists(), s.getMembers()))
    users = list(map(lambda x: x.user, profiles))
    if len(users) < 1:
        return None
    user_device_notify(users, f"Results Declared: {competition.title}",
                       f"This is to inform you that the results of '{competition.title}' competition have been declared. You may check your submission ranking now, and don't forget to claim your XP!", competition.get_link)


def resultsDeclaredParticipantAlert(competition: Competition) -> list:
    """
    Notify results to every participant in given competition
    """
    if not competition.resultDeclared:
        return False

    list(map(
        lambda sub: filteredUsers(
            sub, competition), competition.getValidSubmissions()
    ))
    return list(map(
        lambda sub: filteredMails(
            sub, competition), competition.getValidSubmissions()
    ))


def resultsDeclaredJudgeAlert(competition: Competition) -> list:
    """
    Notify results to every judge in given competition
    """
    if not competition.resultDeclared:
        return False
    list(map(
        lambda judge: user_device_notify(competition.judge.user, f"Results Declared: {competition.title}",
                                         f"This is to inform you that the results of '{competition.title}' competition have been declared. This marks the successfull end of this competition. The following link button will lead you to competition results page.", competition.get_link)
        if DeviceNotificationSubscriber.objects.filter(user=competition.judge.user, device_notification__notification__code=NotificationCode.RES_DEC_JUDGE_ALERT).exists() else None, competition.getJudges()))
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
        )if EmailNotificationSubscriber.objects.filter(user=competition.judge.user, email_notification__notification__code=NotificationCode.RES_DEC_JUDGE_ALERT).exists() else None, competition.getJudges()
    ))


def resultsDeclaredModeratorAlert(competition: Competition) -> str:
    """
    Notify results to the moderator in given competition
    """
    if not competition.resultDeclared:
        return False
    device, email = False, False
    mod = competition.getModerator()
    if DeviceNotificationSubscriber.objects.filter(user=mod.user, device_notification__notification__code=NotificationCode.RES_DEC_MOD_ALERT).exists():
        device = user_device_notify(mod.user, f"Results Declared: {competition.title}",
                           f"This is to inform you that the results of '{competition.title}' competition have been declared. This marks the successfull end of the competition.", {competition.get_link})
    if EmailNotificationSubscriber.objects.filter(user=mod.user, email_notification__notification__code=NotificationCode.RES_DEC_MOD_ALERT).exists():
        email = sendActionEmail(
            to=mod.get_email,
            username=mod.get_name,
            subject=f"Results Declared: {competition.title}",
            header=f"This is to inform you that the results of '{competition.title}' competition have been declared. This marks the successfull end of the competition.",
            actions=[{
                'text': 'View results',
                'url': f"{competition.get_link}?tab=4"
            }],
            footer=f"The results were based on aggregated markings by independent judgement panel. All participants will be informed shortly. Thank you for ensuring successful conduction of this competition.",
            conclusion=f"You received this email because you moderated the mentioned competition. If this is an error, then please report to us."
        )
    return device, email
    

def competitionAdmireNotification(profile: Profile, compete: Competition):
    """
    To notify creator of competition that someone has admired their competition
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=compete.creator.user, device_notification__notification__code=NotificationCode.ADMIRED_COMPETITION).exists():
        device = user_device_notify(compete.creator.user, "Competition Admired",
                           f"Your competition - {compete.title} - has been admired by - {profile.getFName()} - ({profile.user})",
                           compete.getLink())

    if EmailNotificationSubscriber.objects.filter(user=compete.creator.user, email_notification__notification__code=NotificationCode.ADMIRED_COMPETITION).exists():
        email = sendActionEmail(
            to=compete.creator.getEmail(),
            username=compete.creator.getFName,
            subject=f"Competition Admired",
            header=f"This is to inform you that your competition - {compete.title} - has been admired by - {profile.getFName()} - ({profile.user}).",
            actions=[{
                'text': 'View Competition',
                'url': compete.get_link
            }],
            footer=f"You can thank and reach out to {profile.getFName()}.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def competitonXpClaimed(profile: Profile, compete: Competition):
    """
    To notify the user that they have claimed their XP from a competition
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.CLAIM_XP_COMPETITION).exists():
        device = user_device_notify(profile.user, "Competition XP Claimed",
                           f"You have claimed XP from competition - {compete.title}",
                           compete.getLink())

    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.CLAIM_XP_COMPETITION).exists():
        email = sendActionEmail(
            to=profile.getEmail(),
            username=profile.getFName,
            subject=f"Competition XP Claimed",
            header=f"This is to inform you that you have claimed XP from competition - {compete.title} -.",
            actions=[{
                'text': 'View Competition',
                'url': compete.get_link
            }],
            footer=f"Thank you for participating. We hope that you keep participating in future competitions.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email
