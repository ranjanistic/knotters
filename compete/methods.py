from os import path as os_path
from uuid import UUID, uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from django.utils import timezone
from main.env import ISTESTING, SITE
from main.methods import errorLog, renderString, renderView
from main.strings import Compete, Message, url
from people.models import Profile, User
from PIL import Image, ImageDraw, ImageFont
from qrcode import make

from .apps import APPNAME
from .mailers import certsAllotedAlert, resultsDeclaredAlert
from .models import (AppreciationCertificate, Competition,
                     ParticipantCertificate, Result, Submission,
                     SubmissionParticipant)


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Renders view for competition module, with appropriate preset data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file name (inside compete directory) of the view to be rendered.
        data (dict, optional): The data to be passed to the view. Defaults to dict().

    Returns:
        HttpResponse: The rendered view.
    """
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstrResponse(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Returns HttpResponse of html string of view for competition module, with appropriate preset data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file name (inside compete directory) of the view to be rendered.
        data (dict, optional): The data to be passed to the view. Defaults to dict().

    Returns:
        HttpResponse: The http response of the rendered html.
    """
    return HttpResponse(rendererstr(request, file, data))


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    """Returns string form of html for the view of competition module, with appropriate preset data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file name (inside compete directory) of the view to be rendered.
        data (dict, optional): The data to be passed to the view. Defaults to dict().

    Returns:
        str: The html string of the view.
    """
    return renderString(request, file, data, fromApp=APPNAME)


def getIndexSectionHTML(section: str, request: WSGIRequest) -> str:
    """Returns html for the given section of comeptition index page.

    Args:
        section (str): The section name as per main.strings.Compete attributes.
        request (WSGIRequest): The request object.

    Returns:
        str: The html string.
    """
    try:
        now = timezone.now()
        data = dict()
        cacheKey = f"{APPNAME}_{section}"
        if section == Compete.ACTIVE:
            try:
                actives = Competition.objects.filter(
                    startAt__lte=now, endAt__gt=now, is_draft=False).order_by('-endAt')
            except:
                actives = list()
            data[Compete.ACTIVE] = actives
        elif section == Compete.UPCOMING:
            try:
                upcomings = Competition.objects.filter(
                    startAt__gt=now, is_draft=False).order_by('-startAt')
            except:
                upcomings = list()
            data[Compete.UPCOMING] = upcomings
        elif section == Compete.HISTORY:
            history = cache.get(cacheKey, [])
            if not len(history):
                history = Competition.objects.filter(
                    endAt__lte=now, hidden=False, is_draft=False).order_by('-endAt')
                cache.set(cacheKey, history, settings.CACHE_MINI)
            data[Compete.HISTORY] = history
        else:
            return False
        return rendererstr(request, f'index/{section}', data)
    except:
        return False


def competitionProfileData(request: WSGIRequest, compID: UUID = None, nickname: str = None) -> dict:
    """Returns competition profile data.
    Needs only one of compID or nickname.
    If compID and nickname both are provided, nickname will be preferred.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID, optional): The competition id. Defaults to None.
        nickname (str, optional): The nickname of the user. Defaults to None.

    Raises:
        ObjectDoesNotExist: If the any requested info is not returnable.

    Returns:
        dict: The competition profile data.
    """
    try:
        cacheKey = f"{APPNAME}_competition_profile"
        if nickname:
            cacheKey = f"{cacheKey}_{nickname}"
            compete = cache.get(cacheKey, None)
            if not compete:
                compete = Competition.objects.get(nickname=nickname)
                cache.set(cacheKey, compete, settings.CACHE_MICRO)
        else:
            cacheKey = f"{cacheKey}_{compID}"
            compete = cache.get(cacheKey, None)
            if not compete:
                compete = Competition.objects.get(id=compID)
                cache.set(cacheKey, compete, settings.CACHE_MICRO)

        isManager = request.user.is_authenticated and compete.creator == request.user.profile
        if compete.is_draft and not isManager:
            raise ObjectDoesNotExist('isdraft: ', compete)

        if request.user.is_authenticated:
            data = dict(
                compete=compete,
                isJudge=compete.isJudge(request.user.profile),
                isMod=compete.isModerator(request.user.profile),
                isManager=isManager
            )
        else:
            data = dict(
                compete=compete
            )
        return data
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False


def getCompetitionSectionData(section: str, competition: Competition, user: User) -> dict:
    """Returns competition section data.

    Args:
        section (str): The section name as per main.strings.Compete attributes.
        competition (Competition): The competition object.
        user (User): The requesting user object.

    Returns:
        dict: The competition section data.
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
            if competition.isNotAllowedToParticipate(profile, False):
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
    """Returns html for the given section of competition page.

    Args:
        competition (Competition): The competition object instance of which the data will be provided.
        section (str): The section name as per main.strings.Compete attributes.
        request (WSGIRequest): The request object.

    Returns:
        str: The html string.
    """
    if not Compete().COMPETE_SECTIONS.__contains__(section):
        return False
    data = dict()
    for sec in Compete().COMPETE_SECTIONS:
        if sec == section:
            data = getCompetitionSectionData(sec, competition, request.user)
            break
    return rendererstr(request, f'profile/{section}', data)


def generateCertificate(certname: str, certID: str, userdisplayname: str, compname: str, abouttext: str, associate: str = None, template: str = 'certificate') -> str:
    """
    Generates a certificate for the given user.
    NOTE: This method depends on dimensions of the template images. If they're changed, then the coordinates utilized in this method
        will also require modifications accordingly.

    Args:
        certname (str): The name of the certificate.
        certID (str): The ID of the certificate.
        userdisplayname (str): The display name of the user.
        compname (str): The name of the competition.
        abouttext (str): The sub-text to be displayed in the certificate. Can be the date of the competition.
        associate (ImageFile, optional): The associate image file instance. Defaults to None.
        template (str, optional): The certificate template name. Defaults to 'certificate'. Expects the file at templates/<template>.jpg

    Returns:
        str: Path of generated certificate, pdf. (similar for jpg format)
    """
    imagex = 5100
    imagey = 3300
    font_dir = 'templates/poppins-500.ttf'
    body_font_dir = 'templates/questrial-400.ttf'
    cert_dir = f'templates/{template}.jpg'
    name_font = ImageFont.truetype(
        os_path.join(settings.BASE_DIR, font_dir), 225)
    comp_font = ImageFont.truetype(
        os_path.join(settings.BASE_DIR, font_dir), 175)
    about_font = ImageFont.truetype(
        os_path.join(settings.BASE_DIR, font_dir), 88)
    id_font = ImageFont.truetype(os_path.join(
        settings.BASE_DIR, body_font_dir), 58)
    namexy = (imagex-name_font.getsize(userdisplayname)[0]-240, 688)
    compxy = (imagex-comp_font.getsize(compname)[0]-240, 1284)
    aboutxy = (imagex-about_font.getsize(abouttext)[0]-240, 1610)
    idxy = (44, 3188)
    qrxy = (44, 44)
    certpath = f"{APPNAME}/certificates/{certname}.pdf"
    certpathimg = f"{APPNAME}/certificates/{certname}.jpg"
    qrimage = make(
        f"{SITE}{url.getRoot(APPNAME)}{url.compete.CERT_VERIFY}?id={certID}")
    qrimage = qrimage.resize((694, 694), Image.ANTIALIAS)
    if not ISTESTING:
        certimage = Image.open(os_path.join(settings.BASE_DIR, cert_dir))
        image_editable = ImageDraw.Draw(certimage)
        image_editable.text(xy=namexy, text=userdisplayname, fill=(
            0, 0, 0), font=name_font, align='right')
        image_editable.text(xy=compxy, text=compname, fill=(
            0, 0, 0), font=comp_font, align='right')
        image_editable.text(xy=aboutxy, text=abouttext, fill=(
            0, 0, 0), font=about_font, align='right')
        image_editable.text(xy=idxy, text=str(
            certID).upper(), fill=(0, 0, 0), font=id_font)
        certimage.paste(qrimage, qrxy)
        if associate:
            assxy = (2425, 2825)
            assimage = Image.open(os_path.join(
                settings.MEDIA_ROOT, str(associate)))
            assimage = assimage.resize((1482, 450), Image.ANTIALIAS)
            certimage.paste(assimage, assxy)
        certimage.save(os_path.join(
            settings.MEDIA_ROOT, certpath), save_all=True)
        certimage.save(os_path.join(settings.MEDIA_ROOT, certpathimg))
    return certpath


def prepareNameForCertificate(name: str, fname: str, lname: str) -> str:
    """
    Prepares the display name of user for certificate. (Long names are shortened to initials, and are capitalized)

    Args:
        name (str): The name of the user.
        fname (str): The first name of the user.
        lname (str): The last name of the user.

    Returns:
        str: The name to be displayed on certificate.
    """
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
            i += 1
    if len(name) > 30:
        name = name[:(30-len(name))]
    return name


def generateParticipantCertificate(profile: Profile, result: Result, certID: UUID) -> str:
    """
    Generates a certificate for the given participant.

    Args:
        profile (Profile): The profile instance of the participant.
        result (Result): The result instance of the participant.
        certID (UUID): The ID of the certificate.

    Returns:
        str, bool: Path of generated certificate, pdf. (similar for jpg format), if successful. False otherwise.
    """
    try:
        name = prepareNameForCertificate(
            profile.getName(), profile.getFName(), profile.getLName())

        comp = result.competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]
        about = f"from {result.competition.startAt.strftime('%B')} {result.competition.startAt.day}, {result.competition.startAt.year} to {result.competition.endAt.strftime('%B')} {result.competition.endAt.day}, {result.competition.endAt.year}"
        return generateCertificate(
            certname=f"{result.competition.getID()}-{profile.getUserID()}",
            certID=certID,
            userdisplayname=name,
            compname=comp,
            abouttext=about,
            associate=result.competition.associate,
            template='certificate'
        )
    except Exception as e:
        errorLog(e)
        return False


def generateJudgeCertificate(judge: Profile, competition: Competition, certID: UUID) -> str:
    """
    Generates a certificate for the given judge.

    Args:
        judge (Profile): The profile instance of the judge.
        competition (Competition): The competition instance.
        certID (UUID): The ID of the certificate.

    Returns:
        str, bool: Path of generated certificate, pdf. (similar for jpg format), if successful. False otherwise.
    """
    try:
        name = prepareNameForCertificate(
            judge.getName(), judge.getFName(), judge.getLName())
        comp = competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]
        about = f"from {competition.startAt.strftime('%B')} {competition.startAt.day}, {competition.startAt.year} to {competition.endAt.strftime('%B')} {competition.endAt.day}, {competition.endAt.year}"
        return generateCertificate(
            certname=f"{competition.getID()}-{judge.getUserID()}",
            certID=certID,
            userdisplayname=name,
            compname=comp,
            abouttext=about,
            associate=competition.associate,
            template='certificate-judge'
        )
    except Exception as e:
        errorLog(e)
        return False


def generateModCertificate(competition: Competition, certID: UUID) -> str:
    """Generates a certificate for moderator of the given competition.

    Args:
        competition (Competition): The competition instance.
        certID (UUID): The ID of the certificate.

    Returns:
        str, bool: Path of generated certificate, pdf. (similar for jpg format), if successful. False otherwise.
    """
    try:
        mod = competition.moderator()
        name = prepareNameForCertificate(
            mod.getName(), mod.getFName(), mod.getLName())

        comp = competition.title
        if len(comp) > 39:
            comp = comp[:(39-len(comp))]
        about = f"from {competition.startAt.strftime('%B')} {competition.startAt.day}, {competition.startAt.year} to {competition.endAt.strftime('%B')} {competition.endAt.day}, {competition.endAt.year}"
        return generateCertificate(
            certname=f"{competition.getID()}-{mod.getUserID()}",
            certID=certID,
            userdisplayname=name,
            compname=comp,
            abouttext=about,
            associate=competition.associate,
            template='certificate-mod'
        )
    except Exception as e:
        errorLog(e)
        return False


def DeclareResults(competition: Competition) -> str:
    """Declairs the results of the competition, adds results alerts email task to the queue.

    Args:
        competition (Competition): The competition instance.

    Raises:
        Exception, bool: If the results are not declared, an exception is raised, otherwise True is returned.
    """
    taskKey = competition.CACHE_KEYS.result_declaration_task
    cache.set(taskKey, Message.RESULT_DECLARING, settings.CACHE_ETERNAL)
    declared = competition.declareResults()
    if not declared:
        cache.delete(taskKey)
        raise Exception(f'Result declaration failed!', competition)
    cache.set(taskKey, Message.RESULT_DECLARED, settings.CACHE_ETERNAL)
    return resultsDeclaredAlert(declared)


def AllotCompetitionCertificates(results: list, competition: Competition) -> bool:
    """Allots certificates to the participants of the competition and also to the judges and moderator.

    Args:
        results (list): List of results instances of the competition.
        competition (Competition): The competition instance.

    Returns:
        bool: True if all certificates are allotted, False if exceptions are raised.
    """
    try:
        taskKey = competition.CACHE_KEYS.certificates_allotment_task
        cache.set(taskKey,
                  Message.CERTS_GENERATING, settings.CACHE_ETERNAL)
        appreciateeCerts = []
        id = uuid4()
        certificate = generateModCertificate(competition, id.hex)
        if not certificate:
            cache.delete(taskKey)
            raise Exception(f"Couldn't generate certificate (mod)!",
                            competition.moderator(), competition)
        appreciateeCerts.append(
            AppreciationCertificate(
                id=id,
                competition=competition,
                appreciatee=competition.moderator(),
                certificate=certificate
            )
        )
        for judge in competition.getJudges():
            id = uuid4()
            certificate = generateJudgeCertificate(judge, competition, id.hex)
            if not certificate:
                cache.delete(
                    taskKey)
                raise Exception(
                    f"Couldn't generate certificate (judge)!", judge, competition)
            appreciateeCerts.append(
                AppreciationCertificate(
                    id=id,
                    competition=competition,
                    appreciatee=judge,
                    certificate=certificate
                )
            )
        AppreciationCertificate.objects.bulk_create(
            appreciateeCerts, ignore_conflicts=True)
        participantCerts = []
        for result in results:
            for member in result.getMembers():
                id = uuid4()
                certificate = generateParticipantCertificate(
                    member, result, id.hex)
                if not certificate:
                    cache.delete(
                        taskKey)
                    raise Exception(
                        f"Couldn't generate certificate (participant)!", member, competition)
                participantCerts.append(
                    ParticipantCertificate(
                        id=id,
                        result=result,
                        profile=member,
                        certificate=certificate
                    )
                )
        ParticipantCertificate.objects.bulk_create(
            participantCerts, batch_size=100, ignore_conflicts=True)
        cache.set(taskKey,
                  Message.CERTS_GENERATED, settings.CACHE_ETERNAL)
        certsAllotedAlert(competition)
        return True
    except Exception as e:
        errorLog(e)
        cache.delete(taskKey)
        return False
