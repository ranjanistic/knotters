from django.utils import timezone
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.core.handlers.wsgi import WSGIRequest
from main.methods import renderView, renderString, classAttrsToDict
from main.strings import Compete, url, setPathParams
from people.models import User
from .models import Competition, SubmissionParticipant, Result, Submission
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = {}) -> HttpResponse:
    data['URLS'] = {}

    def cond(key, value):
        return str(key).isupper()

    urls = classAttrsToDict(url.Compete, cond)

    for key in urls:
        data['URLS'][key] = f"{url.getRoot(APPNAME)}{setPathParams(urls[key])}"
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
            print(actives)
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


def getCompetitionSectionData(section: str, competition: Competition, user: User) -> dict:
    """
    Returns section (tab) data for the given competition.
    
    :section: The section name as per main.strings.Compete attributes.
    :competition: The competition object instance of which the data will be provided.
    :user: The requesting user (anonymous allowed)
    """
    data = dict(compete=competition)
        
    if section == Compete.OVERVIEW:
        pass
    elif section == Compete.TASK:
        pass
    elif section == Compete.GUIDELINES:
        pass
    elif section == Compete.SUBMISSION:
        profile = user.profile
        try:
            submission = Submission.objects.get(
                competition=competition, members=profile)
            relation = SubmissionParticipant.objects.get(
                submission=submission, profile=profile)
            data['submission'] = submission
            data['confirmed'] = relation.confirmed
        except:
            data['submission'] = None
    elif section == Compete.RESULT:
        profile = user.profile
        if not competition.resultDeclared:
            data['results'] = None
        else:
            results = Result.objects.filter(
                competition=competition).order_by('rank')
            if user.is_authenticated:
                memberfound = False
                for res in results:
                    if res.submission.isMember(profile):
                        memberfound = True
                        if res.rank > 10:
                            data['selfresult'] = res
                        break

                if not memberfound:
                    try:
                        subm = Submission.objects.get(
                            competition=competition, members=profile, valid=False)
                        data['selfInvaildSubmission'] = subm
                    except:
                        pass
            data['results'] = results
    else: return None
    return data


def getCompetitionSectionHTML(competition: Competition, section: str, request: WSGIRequest) -> str:
    if not Compete().COMPETE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in Compete().COMPETE_SECTIONS:
        if sec == section:
            data = getCompetitionSectionData(sec, competition, request.user)
            break
    return renderString(request, f'profile/{section}', data, APPNAME)
