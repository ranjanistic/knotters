import os
import requests
import base64
from uuid import uuid4
import re
import json
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone
from datetime import timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.base import ContentFile, File
from django.db.models.fields.files import ImageFieldFile
from django.http.response import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect, render
from django.conf import settings
from allauth.account.models import EmailAddress
from management.models import ActivityRecord
from .mailers import sendErrorLog
from .env import ASYNC_CLUSTER, ISDEVELOPMENT, ISTESTING, PUBNAME
from .strings import Code, url, MANAGEMENT, MODERATION, COMPETE, PROJECTS, PEOPLE, DOCS, BYPASS_DEACTIVATION_PATHS, AUTH


def renderData(data: dict = dict(), fromApp: str = str()) -> dict:
    """
    Adds default meta data to the dictionary 'data' which is assumed to be sent with a rendering template.

    :param: fromApp: The subapplication name from whose context this method will return udpated data.
    """
    URLS = dict(**data.get('URLS', dict()), **url.getURLSForClient())
    if data.get('URLS', None):
        del data['URLS']
    if fromApp == str():
        URLS = dict(**URLS, Projects=url.projects.getURLSForClient(), People=url.people.getURLSForClient(),
                    Compete=url.compete.getURLSForClient(), Moderation=url.moderation.getURLSForClient(), Management=url.management.getURLSForClient())
    elif fromApp == PEOPLE:
        URLS = dict(**URLS, **url.people.getURLSForClient(), Projects=url.projects.getURLSForClient(), Compete=url.compete.getURLSForClient(),
                    Moderation=url.moderation.getURLSForClient(), Management=url.management.getURLSForClient())
    elif fromApp == PROJECTS:
        URLS = dict(**URLS, **url.projects.getURLSForClient(), People=url.people.getURLSForClient(), Compete=url.compete.getURLSForClient(),
                    Moderation=url.moderation.getURLSForClient(), Management=url.management.getURLSForClient())
    elif fromApp == COMPETE:
        URLS = dict(**URLS, **url.compete.getURLSForClient(), People=url.people.getURLSForClient(), Projects=url.projects.getURLSForClient(),
                    Moderation=url.moderation.getURLSForClient(), Management=url.management.getURLSForClient())
    elif fromApp == MODERATION:
        URLS = dict(**URLS, **url.moderation.getURLSForClient(), Projects=url.projects.getURLSForClient(),
                    People=url.people.getURLSForClient(), Compete=url.compete.getURLSForClient(), Management=url.management.getURLSForClient())
    elif fromApp == MANAGEMENT:
        URLS = dict(**URLS, **url.management.getURLSForClient(), Projects=url.projects.getURLSForClient(),
                    People=url.people.getURLSForClient(), Compete=url.compete.getURLSForClient(), Moderation=url.moderation.getURLSForClient())
    elif fromApp == DOCS:
        URLS = dict(**URLS, **url.docs.getURLSForClient(), Projects=url.projects.getURLSForClient(), Management=url.management.getURLSForClient(),
                    People=url.people.getURLSForClient(), Compete=url.compete.getURLSForClient(), Moderation=url.moderation.getURLSForClient())

    URLS = dict(**URLS, Docs=url.docs.getURLSForClient(),
                Auth=url.auth.getURLSForClient())

    return dict(**data, URLS=URLS, ROOT=url.getRoot(fromApp), SUBAPPNAME=fromApp)


def renderView(request: WSGIRequest, view: str, data: dict = dict(), fromApp: str = str()) -> HttpResponse:
    """
    Returns text/html data as http response via given template view name.

    :view: The template view name (without extension), under the fromApp named folder
    :data: The dict data to be render in the view.
    :fromApp: The subapplication division name under which the given view named template file resides
    """

    return render(request, f"{str() if fromApp == str() else f'{fromApp}/' }{view}.html", renderData(data, fromApp))


def renderString(request: WSGIRequest, view: str, data: dict = dict(), fromApp: str = str()) -> str:
    """
    Returns text/html data as string via given template view name.

    :view: The template view name (without extension), under the fromApp named folder.
    :data: The dict data to be render in the view.
    :fromApp: The subapplication division name under which the given view named template file resides
    """
    return render_to_string(f"{str() if fromApp == str() else f'{fromApp}/' }{view}.html", renderData(data, fromApp), request)


def respondJson(code: str, data: dict = dict(), error: str = str(), message: str = str()) -> JsonResponse:
    """
    Returns application/json data as http response.

    :code: A code name, indicating response type.
    :data: The dict data to be sent along with code.
    """

    if error:
        data = dict(**data, error=error)
    if message:
        data = dict(**data, message=message)

    return JsonResponse({
        'code': code,
        **data
    }, encoder=JsonEncoder)


def respondRedirect(fromApp: str = str(), path: str = str(), alert: str = str(), error: str = str()) -> HttpResponseRedirect:
    """
    returns redirect http response, with some parametric modifications.
    """
    return redirect(f"{url.getRoot(fromApp)}{path}{url.getMessageQuery(alert=alert,error=error,otherQueries=(path.__contains__('?') or path.__contains__('&')))}")


def getDeepFilePaths(dir_name: str, appendWhen=None):
    """
    Returns list of mapping of file paths only inside the given directory.

    :appendWhen: a function, with argument as traversed path in loop, should return bool whether given arg path is to be included or not.
    """
    allassets = mapDeepPaths(os.path.join(settings.BASE_DIR, f'{dir_name}/'))
    assets = list()
    for asset in allassets:
        path = str(asset).replace(str(settings.BASE_DIR), str())
        if path.startswith('\\'):
            path = str(path).strip("\\")
        if path.startswith(dir_name):
            path = f"/{path}"
        if not assets.__contains__(path):
            if appendWhen:
                if appendWhen(path):
                    assets.append(path)
            else:
                assets.append(path)
    return assets


def mapDeepPaths(dir_name, traversed=list(), results=list()):
    """
    Returns list of mapping of paths inside the given directory.
    """
    dirs = os.listdir(dir_name)
    if dirs:
        for f in dirs:
            new_dir = dir_name + f + '/'
            if os.path.isdir(new_dir) and new_dir not in traversed:
                traversed.append(new_dir)
                mapDeepPaths(new_dir, traversed, results)
            else:
                results.append([new_dir[:-1], os.stat(new_dir[:-1])])

    paths = list()
    for file_name, _ in results:
        paths.append(str(file_name).strip('.'))
    return paths


def maxLengthInList(list: list = list()) -> int:
    max = len(str(list[0]))
    for item in list:
        if max < len(str(item)):
            max = len(str(item))
    return max


def minLengthInList(list: list = list()) -> int:
    min = len(str(list[0]))
    for item in list:
        if min > len(str(item)):
            min = len(str(item))
    return min


def base64ToImageFile(base64Data: base64) -> File:
    try:
        format, imgstr = base64Data.split(';base64,')
        ext = format.split('/')[-1]
        if not ['jpg', 'png', 'jpeg'].__contains__(ext):
            return False
        return ContentFile(base64.b64decode(imgstr), name=f"{uuid4().hex}.{ext}")
    except Exception as e:
        return None

def base64ToFile(base64Data: base64) -> File:
    try:
        format, filestr = base64Data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(filestr), name=f"{uuid4().hex}.{ext}")
    except Exception as e:
        errorLog(e)
        return None


class JsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImageFieldFile):
            return str(obj)
        return super(JsonEncoder, self).default(obj)

def errorLog(error, raiseErr=True):
    if not ISTESTING:
        try:
            with open(os.path.join(os.path.join(settings.BASE_DIR, '_logs_'), 'errors.txt'), 'a') as log_file:
                log_file.write(f"\n{timezone.now()}\n{error}")
            addMethodToAsyncQueue(f"main.mailers.{sendErrorLog.__name__}", error)
        except Exception as e:
            print('Error in logging: ', e)
            if not ISDEVELOPMENT:
                print('Log: ', error)
        if ISDEVELOPMENT:
            if raiseErr:
                raise Exception(error)
            else: print(error)


def getNumberSuffix(value: int) -> str:
    valuestr = str(value)
    if value == 1:
        return 'st'
    elif value == 2:
        return 'nd'
    elif value == 3:
        return 'rd'
    else:
        if value > 9:
            if valuestr[len(valuestr) - 2] == "1" or valuestr[len(valuestr) - 1] == "0":
                return "th"
            return getNumberSuffix(value=int(valuestr[len(valuestr) - 1]))
        else:
            return "th"


def verify_captcha(recaptcha_response: str) -> bool:
    try:
        resp = requests.post(settings.GOOGLE_RECAPTCHA_VERIFY_SITE, dict(
            secret=settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            response=recaptcha_response
        ))
        result = resp.json()
        return result['success']
    except Exception as e:
        errorLog(e)
        return False


def addMethodToAsyncQueue(methodpath, *params):
    try:
        if ASYNC_CLUSTER:
            from django_q.tasks import async_task
            async_task(methodpath, *params)
        else:
            import main
            import people
            import projects
            import management
            import moderation
            import compete
            eval(f"{methodpath}{params}", dict(main=main, people=people, projects=projects,
                 management=management, moderation=moderation, compete=compete))
        return True
    except Exception as e:
        errorLog(e)
        return False


def testPathRegex(pathreg, path):
    localParamRegex = "[a-zA-Z0-9\. \\-\_\%]"
    regpath = re.sub(Code.URLPARAM, f"+{localParamRegex}+", pathreg)
    if regpath == path:
        return True
    parts = regpath.split("+")
    parts.pop()

    def eachpart(part: str):
        return localParamRegex if part == localParamRegex else f"({part})"
    finalreg = "+".join(map(eachpart, parts))
    match = re.compile(finalreg).match(path)
    if match:
        return len(match.groups()) > 0
    return False


def allowBypassDeactivated(path):
    path = path.split('?')[0]
    for pathreg in BYPASS_DEACTIVATION_PATHS:
        if (testPathRegex(pathreg, path)):
            return True
    return False


def addActivity(view, user, request_get, request_post, status):
    print(request_post)
    ActivityRecord.objects.create(view_name=view, user=user, request_get=json.dumps(
        request_get), request_post=json.dumps(request_post), response_status=status)


def activity(request, response):
    print(request.POST)
    addMethodToAsyncQueue(f"main.methods.{addActivity.__name__}", request.path,
                          request.user, request.GET.__dict__, request.POST, response.status_code)

# def alertUnverified():
#     from .mailers import sendActionEmail
#     emails = EmailAddress.objects.filter(
#         verified=False,
#         primary=True,
#         user__date_joined__lte=(timezone.now()+timedelta(days=-2)),
#     )
#     for email in emails:
#         sendActionEmail(
#             username=email.user.first_name,
#             to=email.user.email,
#             subject="Unverified account",
#             header=f"Please login to verify your account at {PUBNAME}, or else your unverified account will be deleted automatically in two days.",
#             footer=f"This is done to prevent spam accounts on our platform, and if you're reading this, please verify your account asap.",
#             conclusion=f"This an alert about your unverified account at {PUBNAME}. If this is unfamiliar, then you don't need to worry.",
#             actions=[dict(
#                 text='Login to continue',
#                 url=f'{url.getRoot(AUTH)}{url.Auth.LOGIN}'
#             )]
#         )

def removeUnverified():
    from people.models import Profile, User
    time = timezone.now() + timedelta(days=-4)
    users = EmailAddress.objects.filter(
        verified=False,
        primary=True,
        user__date_joined__lte=time
    ).values_list('user', flat=True)
    if not EmailAddress.objects.filter(user__id__in=list(users),verified=True).exists():
        profs = Profile.objects.filter(user__id__in=list(users)).delete()
        delusers = User.objects.filter(id__in=list(users)).delete()
        return delusers, profs
    return False
