from django.core.handlers.wsgi import WSGIRequest
import os
from PIL import Image, ImageFont, ImageDraw
from django.utils import timezone
from django.http.response import HttpResponse
from main.methods import base64ToImageFile, errorLog, renderView, renderString
from main.strings import Compete
from main.env import ISTESTING
from people.models import User, Profile
from django.conf import settings
from .models import Competition, SubmissionParticipant, Result, Submission
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderString(request, file, data, fromApp=APPNAME)


def getIndexSectionHTML(section: str, request: WSGIRequest) -> str:
    try:
        now = timezone.now()
        data = dict()
        if section == Compete.ACTIVE:
            try:
                actives = Competition.objects.filter(
                    startAt__lte=now, endAt__gt=now).order_by('-endAt')
            except:
                actives = list()
            data[Compete.ACTIVE] = actives
        elif section == Compete.UPCOMING:
            try:
                upcomings = Competition.objects.filter(
                    startAt__gt=now).order_by('-startAt')
            except:
                upcomings = list()
            data[Compete.UPCOMING] = upcomings
        elif section == Compete.HISTORY:
            try:
                history = Competition.objects.filter(
                    endAt__lte=now).order_by('-endAt')
            except:
                history = list()
            data[Compete.HISTORY] = history
        else:
            return False
        return rendererstr(request, f'index/{section}', data)
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
        try:
            profile = user.profile
            relation = SubmissionParticipant.objects.get(
                submission__competition=competition, profile=profile)
            data['submission'] = relation.submission
            data['confirmed'] = relation.confirmed
        except:
            data['submission'] = None
    elif section == Compete.RESULT:
        if not competition.resultDeclared:
            data['results'] = None
        else:
            results = Result.objects.filter(
                competition=competition).order_by('rank')
            if user.is_authenticated:
                profile = user.profile
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
    else:
        return None
    return data


def getCompetitionSectionHTML(competition: Competition, section: str, request: WSGIRequest) -> str:
    if not Compete().COMPETE_SECTIONS.__contains__(section):
        return False
    data = dict()
    for sec in Compete().COMPETE_SECTIONS:
        if sec == section:
            data = getCompetitionSectionData(sec, competition, request.user)
            break
    return rendererstr(request, f'profile/{section}', data)

def generateCertificate(profile:Profile,result:Result):
    """
    Returns certificate images for profile's result.
    """
    try:
        certimage = Image.open(os.path.join(settings.BASE_DIR, 'templates/certificate.jpg'))
        head_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'templates/poppins-500.ttf'), 100)
        body_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, 'templates/questrial-400.ttf'), 50)
        image_editable = ImageDraw.Draw(certimage)
        image_editable.text((15,15), profile.getName(), (237, 230, 211), font=head_font)
        image_editable.text((55,85), result.competition.title, (237, 230, 211), font=head_font)
        image_editable.text((55,85), result.getRank(), (237, 230, 211), font=head_font)
        image_editable.text((55,85), str(result.competition.startAt), (237, 230, 211), font=body_font)
        image_editable.text((55,85), str(result.competition.endAt), (237, 230, 211), font=body_font)
        certpath = f"{APPNAME}/certificates/{result.competition.getID()}-{profile.getUserID()}.jpg"
        if not ISTESTING:
            certimage.save(os.path.join(settings.BASE_DIR, f"{settings.MEDIA_URL.strip('/')}/{certpath}"))
        return certpath
    except Exception as e:
        print(e)
        errorLog(e)
        return False

from .receivers import *