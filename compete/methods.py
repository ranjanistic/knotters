from django.utils import timezone
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from main.methods import renderView, renderData
from main.strings import compete
from .models import Competition, SubmissionParticipant, Result, Submission
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = {}) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def getIndexSectionHTML(section: str, request: WSGIRequest) -> str:
    try:
        now = timezone.now()
        data = {}
        if section == 'active':
            try:
                actives = Competition.objects.filter(
                    startAt__lte=now, endAt__gt=now).order_by('-endAt')
            except:
                actives = []
            data['actives'] = actives
        elif section == 'upcoming':
            try:
                upcomings = Competition.objects.filter(
                    startAt__gt=now).order_by('-startAt')
            except:
                upcomings = []
            data['upcomings'] = upcomings
        elif section == 'history':
            try:
                history = Competition.objects.filter(
                    endAt__lte=now).order_by('-endAt')
            except:
                history = []
            data['history'] = history
        else:
            return False
        return render_to_string(f'{APPNAME}/index/{section}.html', data, request=request)
    except:
        return False


def getCompetitionSectionData(section: str, competition: Competition, request: WSGIRequest) -> dict:
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
            submission = Submission.objects.get(
                competition=competition, members=request.user.profile)
            relation = SubmissionParticipant.objects.get(
                submission=submission, profile=request.user.profile)
            data['submission'] = submission
            data['confirmed'] = relation.confirmed
        except:
            data['submission'] = None
    if section == compete.RESULT:
        results = Result.objects.filter(
            competition=competition).order_by('rank')
        if request.user.is_authenticated:
            memberfound = False
            for res in results:
                if res.submission.isMember(request.user.profile):
                    memberfound = True
                    if res.rank > 10:
                        data['selfresult'] = res
                    break

            if not memberfound:
                try:
                    subm = Submission.objects.get(
                        competition=competition, members=request.user.profile, valid=False)
                    data['selfInvaildSubmission'] = subm
                except:
                    pass

        data['results'] = results
    return data


def getCompetitionSectionHTML(competition: Competition, section: str, request: WSGIRequest) -> str:
    if not compete.COMPETE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in compete.COMPETE_SECTIONS:
        if sec == section:
            data = getCompetitionSectionData(sec, competition, request)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)
