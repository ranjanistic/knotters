from django.core.handlers.wsgi import WSGIRequest
from qrcode import make
from uuid import UUID, uuid4
import os
from django.core.cache import cache
from PIL import Image, ImageFont, ImageDraw
from django.utils import timezone
from django.http.response import HttpResponse
from main.methods import addMethodToAsyncQueue, errorLog, renderView, renderString
from main.strings import Compete, Message, url
from main.env import ISTESTING, SITE
from people.models import User, Profile
from django.conf import settings
from .models import Competition, ParticipantCertificate, AppreciationCertificate, SubmissionParticipant, Result, Submission
from .mailers import resultsDeclaredAlert, certsAllotedAlert
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)

def rendererstrResponse(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(rendererstr(request, file, data))

def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> str:
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
                    endAt__lte=now, hidden=False).order_by('-endAt')
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
        except Exception as e:
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

def generateCertificate(certname:str, certID, username, compname, abouttext, associate=None, template='certificate'):
    imagex = 1632
    imagey = 1056
    font_dir = 'templates/poppins-500.ttf'
    body_font_dir = 'templates/questrial-400.ttf'
    cert_dir = f'templates/{template}.jpg'
    name_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, font_dir), 72)
    comp_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, font_dir), 56)
    about_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, font_dir), 28)
    id_font = ImageFont.truetype(os.path.join(settings.BASE_DIR, body_font_dir), 18)
    namexy = (imagex-name_font.getsize(username)[0]-77, 220)
    compxy = (imagex-comp_font.getsize(compname)[0]-77, 411)
    aboutxy = (imagex-about_font.getsize(abouttext)[0]-77, 515)
    idxy = (14,1020)
    qrxy = (14,14)
    certpath = f"{APPNAME}/certificates/{certname}.pdf"
    certpathimg = f"{APPNAME}/certificates/{certname}.jpg"
    qrimage = make(f"{SITE}{url.getRoot(APPNAME)}{url.compete.CERT_VERIFY}?id={certID}")
    qrimage = qrimage.resize((222,222),Image.ANTIALIAS)
    if not ISTESTING:
        certimage = Image.open(os.path.join(settings.BASE_DIR, cert_dir))
        image_editable = ImageDraw.Draw(certimage)
        image_editable.text(xy=namexy, text=username, fill=(0, 0, 0), font=name_font, align='right')
        image_editable.text(xy=compxy, text=compname, fill=(0, 0, 0), font=comp_font, align='right')
        image_editable.text(xy=aboutxy, text=abouttext, fill=(0, 0, 0), font=about_font,align='right')
        image_editable.text(xy=idxy, text=str(certID).upper(), fill=(0, 0, 0), font=id_font)
        certimage.paste(qrimage, qrxy)
        if associate:
            assxy = (776,904)
            assimage = Image.open(os.path.join(settings.MEDIA_ROOT, str(associate)))
            assimage = assimage.resize((474,144),Image.ANTIALIAS)
            certimage.paste(assimage, assxy)
        certimage.save(os.path.join(settings.MEDIA_ROOT, certpath), save_all=True)
        certimage.save(os.path.join(settings.MEDIA_ROOT, certpathimg))
    return certpath

def prepareNameForCertificate(name, fname, lname):
    if len(name) > 30:
        name = fname.capitalize()
        lastnames = lname.split(" ")
        i = 1
        for last in lastnames:
            if str(last).strip():
                if i == len(lastnames):
                    if len(f"{name} {last}") < 31:
                        name = f"{name} {last.capitalize()}"
                    else:
                        name = f"{name} {str(last[0]).upper()}."
                else:
                    name = f"{name} {str(last[0]).upper()}."
            i+=1
    if len(name) > 30:
        name = name[:(30-len(name))]
    return name

def generateParticipantCertificate(profile:Profile,result:Result, certID: UUID) -> str:
    """
    Generates certificate for profile's result, and returns generated path.
    """
    try:
        name = prepareNameForCertificate(profile.getName(),profile.getFName(),profile.getLName())

        comp = result.competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]
        about = f"from {result.competition.startAt.strftime('%B')} {result.competition.startAt.day}, {result.competition.startAt.year} to {result.competition.endAt.strftime('%B')} {result.competition.endAt.day}, {result.competition.endAt.year}"
        return generateCertificate(
            certname=f"{result.competition.getID()}-{profile.getUserID()}",
            certID=certID,
            username=name,
            compname=comp,
            abouttext=about,
            associate=result.competition.associate,
            template='certificate'
        )
    except Exception as e:
        errorLog(e)
        return False

def generateJudgeCertificate(judge:Profile,competition:Competition, certID: UUID) -> str:
    """
    Generates certificate for competition's judge, and returns generated path.
    """
    try:
        name = prepareNameForCertificate(judge.getName(),judge.getFName(),judge.getLName())
        
        comp = competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]
        about = f"from {competition.startAt.strftime('%B')} {competition.startAt.day}, {competition.startAt.year} to {competition.endAt.strftime('%B')} {competition.endAt.day}, {competition.endAt.year}"
        return generateCertificate(
            certname=f"{competition.getID()}-{judge.getUserID()}",
            certID=certID,
            username=name,
            compname=comp,
            abouttext=about,
            associate=competition.associate,
            template='certificate-judge'
        )
    except Exception as e:
        errorLog(e)
        return False

def generateModCertificate(competition:Competition, certID: UUID) -> str:
    """
    Generates certificate for competition's mod, and returns generated path.
    """
    try:
        mod = competition.moderator
        name = prepareNameForCertificate(mod.getName(),mod.getFName(),mod.getLName())

        comp = competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]
        about = f"from {competition.startAt.strftime('%B')} {competition.startAt.day}, {competition.startAt.year} to {competition.endAt.strftime('%B')} {competition.endAt.day}, {competition.endAt.year}"
        return generateCertificate(
            certname=f"{competition.getID()}-{mod.getUserID()}",
            certID=certID,
            username=name,
            compname=comp,
            abouttext=about,
            associate=competition.associate,
            template='certificate-mod'
        )
    except Exception as e:
        errorLog(e)
        return False

def DeclareResults(competition:Competition):
    cache.set(f"results_declaration_task_{competition.get_id}", Message.RESULT_DECLARING, settings.CACHE_ETERNAL)
    declared = competition.declareResults()
    if not declared:
        cache.delete(f"results_declaration_task_{competition.get_id}")
        raise Exception(f'Result declaration failed: {competition.id}')
    cache.set(f"results_declaration_task_{competition.get_id}", Message.RESULT_DECLARED, settings.CACHE_ETERNAL)
    addMethodToAsyncQueue(f"{APPNAME}.mailers.{resultsDeclaredAlert.__name__}", declared)


def AllotCompetitionCertificates(results:list,competition:Competition):
    """
    @async
    """
    print('oif')
    try:
        cache.set(f"certificates_allotment_task_{competition.get_id}", Message.CERTS_GENERATING, settings.CACHE_ETERNAL)
        appreciateeCerts = []
        id = uuid4()
        certificate = generateModCertificate(competition,id.hex)
        print('aah')
        if not certificate:
            cache.delete(f"certificates_allotment_task_{competition.get_id}")
            raise Exception(f"Couldn't generate certificate of {competition.moderator.getName()} (m) for {competition.title}")
        appreciateeCerts.append(
            AppreciationCertificate(
                id=id,
                competition=competition,
                appreciatee=competition.moderator,
                certificate=certificate
            )
        )
        for judge in competition.getJudges():
            id = uuid4()
            certificate = generateJudgeCertificate(judge,competition,id.hex)
            if not certificate:
                cache.delete(f"certificates_allotment_task_{competition.get_id}")
                raise Exception(f"Couldn't generate certificate of {judge.getName()} (j) for {competition.title}")
            appreciateeCerts.append(
                AppreciationCertificate(
                    id=id,
                    competition=competition,
                    appreciatee=judge,
                    certificate=certificate
                )
            )
        AppreciationCertificate.objects.bulk_create(appreciateeCerts)
        participantCerts = []
        for result in results:
            for member in result.getMembers():
                id = uuid4()
                certificate = generateParticipantCertificate(member,result,id.hex)
                if not certificate:
                    cache.delete(f"certificates_allotment_task_{competition.get_id}")
                    raise Exception(f"Couldn't generate certificate of {member.getName()} (p) for {competition.title}")
                participantCerts.append(
                    ParticipantCertificate(
                        id=id,
                        result=result,
                        profile=member,
                        certificate=certificate
                    )
                )
        ParticipantCertificate.objects.bulk_create(participantCerts, batch_size=100)
        cache.set(f"certificates_allotment_task_{competition.get_id}", Message.CERTS_GENERATED, settings.CACHE_ETERNAL)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{certsAllotedAlert.__name__}", competition)
        return True
    except Exception as e:
        errorLog(e)
        cache.delete(f"certificates_allotment_task_{competition.get_id}")
        return False


from .receivers import *
