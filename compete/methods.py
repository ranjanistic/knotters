
from django.template.loader import render_to_string
from main.methods import renderView, sendActionEmail, sendAlertEmail, renderData
from main.strings import compete
from people.models import Profile
from main.env import SITE
from django.utils import timezone
from .models import Competition, Relation, Submission
from .apps import APPNAME

def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


def getIndexSectionHTML(section, request):
    try:
        data = {}
        if section == 'active':
            try:
                actives = Competition.objects.filter(endAt__gt=timezone.now())
            except:
                actives = []
            data['actives'] = actives
        elif section == 'history':
            try:
                history = Competition.objects.filter(endAt__lte=timezone.now())
            except:
                history = []
            data['history'] = history
        else: return False
        return render_to_string(f'{APPNAME}/index/{section}.html', data, request=request)
    except:
        return False


def getCompetitionSectionData(section, competition, request):
    data = renderData({
        'competition': competition
    }, fromApp=APPNAME)
    if section == compete.OVERVIEW:
        return {}
    if section == compete.TASK:
        return {}
    if section == compete.GUIDELINES:
        return {}
    if section == compete.SUBMISSION:
        try:
            submission = Submission.objects.get(competition=competition, members=request.user.profile)
            relation = Relation.objects.get(submission=submission, profile=request.user.profile)
            data['submission'] = submission
            data['confirmed'] = relation.confirmed
        except: 
            data['submission'] = None
    if section == compete.RESULT:
        return {}
    return data


def getCompetitionSectionHTML(competition, section, request):
    if not compete.COMPETE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in compete.COMPETE_SECTIONS:
        if sec == section:
            data = getCompetitionSectionData(sec, competition, request)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)

def sendParticipantInvitationMail(profile: Profile, host: Profile, submission: Submission):
    """
    Email invitation to a user for participation with a submission in a competition.
    """
    return sendActionEmail(
        to=profile.user.email, username=profile.user.first_name, subject='Invitation to Participate Together',
        header=f"{host.user.getName()} ({host.user.email}) has invited you to participate with them in our upcoming competition \'{submission.competition.title}\'.",
        actions=[{'text': "See invitation", 'url': f'{SITE}/{APPNAME}/invitation/{submission.id}/{profile.user.id}'}],
        footer=f"You may accept or deny this invitation. If you won't respond, then this invitation will automatically become invalid at the end of competition, or, upon final submission or cancellation of your invitation by {host.user.getName()}, whichever occurrs earlier.",
        conclusion=f"You can ignore this email if you're not interested. If you're being spammed by this invitation, please report to us by replying to this email."
    )

def sendParticipationWelcomeMail(profile: Profile, submission: Submission):
    """
    Email alert to a participants of a submission notifying their participation confirmation
    """
    return sendActionEmail(
        to=profile.user.email, username=profile.user.first_name, subject=f"Your Participation Confirmed",
        header=f"This is to inform you that you've participated in our '{submission.competition.title}' competition. Great! With a lots of goodluck from Knotters Community, make sure you put your 100% efforts in this.",
        actions=[{'text': "View competition", 'url': f'{SITE}/{submission.competition.getLink()}'}],
        footer=f"If you have other people with you, actively coordinate with them, and if you don't have a team, invite someone. However, if you are a lone wolf, then the community is always there for you.",
        conclusion=f"You recieved this email because you participated in a competition at Knotters. If this is unexpected, please report to us by replying to this email."
    )


def sendSubmissionConfirmedMail(profiles: list, submission: Submission):
    """
    Email alert to all participants of a submission indicating their submission has been submitted successfully.
    """
    for profile in profiles:
        sendAlertEmail(
            to=profile.user.email, username=profile.user.first_name, subject=f"Submission Submitted Successfully",
            header=f"This is to inform you that your submission of participation in '{submission.competition.title}' competition was successfully submitted at {submission.submitOn} (IST Asia/Kolkata).{' Your submission was late.' if submission.late else ''}",
            footer=f"Your submission has been safely kept for review, and the results will be declared for all the submissions we have recieved, together. Till then, chill out! NOTE: We're lenient.",
            conclusion=f"You recieved this email because you participated in a competition at Knotters. If this is unexpected, please report to us by replying to this email."
        )

