from django.core.handlers.wsgi import WSGIRequest
from uuid import UUID
import os
from PIL import Image, ImageFont, ImageDraw
from django.utils import timezone
from django.http.response import HttpResponse
from main.methods import errorLog, renderView, renderString
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
            if competition.isNotAllowedToParticipate(profile):
                return None
                
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
                res = results.filter(submission__members=profile).first()
                if res:
                    data['selfresult'] = res
                else:
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

def generateCertificate(profile:Profile,result:Result, certID: UUID) -> str:
    """
    Generates certificate image for profile's result, and returns generated path.
    """
    try:
        imagex = 1632
        imagey = 1056
        font_dir = 'templates/poppins-500.ttf'
        body_font_dir = 'templates/questrial-400.ttf'
        cert_dir = 'templates/certificate.jpg'
        name_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, font_dir), 72)
        comp_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, font_dir), 56)
        about_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, font_dir), 28)
        id_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, body_font_dir), 18)
        certimage = Image.open(os.path.join(settings.BASE_DIR, cert_dir))
        image_editable = ImageDraw.Draw(certimage)
        name = profile.getName()
        if len(name) > 30:
            name = profile.getFName().capitalize()
            lastnames = profile.getLName().split(" ")
            i = 1
            for last in lastnames:
                if str(last).strip():
                    if i == len(lastnames):
                        if len(f"{name} {last}") < 31:
                            name = f"{name} {last.capitalize()}"
                        else:
                            name = f"{name} {str(last[0]).upper()}. "
                    else:
                        name = f"{name} {str(last[0]).upper()}. "
                i+=1
        if len(name) > 30:
            name = name[:(30-len(name))]
        
        comp = result.competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]

        about = f"from {result.competition.startAt.strftime('%B')} {result.competition.startAt.day}, {result.competition.startAt.year} to {result.competition.endAt.strftime('%B')} {result.competition.endAt.day}, {result.competition.endAt.year}"
        namexy = (imagex-name_font.getsize(name)[0]-77, 220)
        compxy = (imagex-comp_font.getsize(comp)[0]-77, 411)
        aboutxy = (imagex-about_font.getsize(about)[0]-77, 515)
        idxy = (22,1020)
        image_editable.text(xy=namexy, text=name, fill=(0, 0, 0), font=name_font, align='right')
        image_editable.text(xy=compxy, text=comp, fill=(0, 0, 0), font=comp_font, align='right')
        image_editable.text(xy=aboutxy, text=about, fill=(0, 0, 0), font=about_font,align='right')
        image_editable.text(xy=idxy, text=str(certID).upper(), fill=(0, 0, 0), font=id_font)
        if result.competition.associate:
            assxy = (787,904)
            assimage = Image.open(os.path.join(settings.MEDIA_ROOT, result.competition.associate))
            assimage = assimage.resize((467,136),Image.ANTIALIAS)
            certimage.paste(assimage, assxy)

        certpath = f"{APPNAME}/certificates/{result.competition.getID()}-{profile.getUserID()}.pdf"
        certpathimg = f"{APPNAME}/certificates/{result.competition.getID()}-{profile.getUserID()}.jpg"
        if not ISTESTING:
            certimage.save(os.path.join(settings.MEDIA_ROOT, certpath), save_all=True)
            certimage.save(os.path.join(settings.MEDIA_ROOT, certpathimg))
        return certpath
    except Exception as e:
        errorLog(e)
        return False

from .receivers import *