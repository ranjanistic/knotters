import os
import logging
import requests
import base64
from uuid import uuid4
from htmlmin.minify import html_minify
import traceback
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
from webpush import send_user_notification, send_group_notification
from django.shortcuts import redirect, render
from django.conf import settings
from allauth.account.models import EmailAddress
from management.models import ActivityRecord
from .env import ASYNC_CLUSTER, ISDEVELOPMENT, ISTESTING
from .strings import URL, Code, url, MANAGEMENT, MODERATION, COMPETE, PROJECTS, PEOPLE, DOCS, AUTH2, AUTH


def renderData(data: dict = dict(), fromApp: str = str()) -> dict:
    """
    Adds default meta data to the dictionary 'data' which is assumed to be sent with a rendering template.

    :param: fromApp: The subapplication name from whose context this method will return udpated data.
    """
    URLS = dict(**data.get('URLS', dict()), **url.getURLSForClient())
    if data.get('URLS', None):
        del data['URLS']
    applinks = {
        PROJECTS.capitalize(): url.projects.getURLSForClient(),
        PEOPLE.capitalize(): url.people.getURLSForClient(),
        AUTH.capitalize(): url.auth.getURLSForClient(),
        DOCS.capitalize(): url.docs.getURLSForClient(),
        COMPETE.capitalize(): url.compete.getURLSForClient(),
        MODERATION.capitalize(): url.moderation.getURLSForClient(),
        MANAGEMENT.capitalize(): url.management.getURLSForClient()
    }
    URLS = dict(
        **URLS,
        **applinks
    )
    if fromApp == PROJECTS:
        URLS = dict(**URLS, **URLS[PROJECTS.capitalize()])
    if fromApp == PEOPLE:
        URLS = dict(**URLS, **URLS[PEOPLE.capitalize()])
    if fromApp == AUTH2:
        URLS = dict(**URLS, **URLS[AUTH.capitalize()])
    if fromApp == DOCS:
        URLS = dict(**URLS, **URLS[DOCS.capitalize()])
    if fromApp == COMPETE:
        URLS = dict(**URLS, **URLS[COMPETE.capitalize()])
    if fromApp == MODERATION:
        URLS = dict(**URLS, **URLS[MODERATION.capitalize()])
    if fromApp == MANAGEMENT:
        URLS = dict(**URLS, **URLS[MANAGEMENT.capitalize()])

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
    return htmlmin(render_to_string(f"{str() if fromApp == str() else f'{fromApp}/' }{view}.html", renderData(data, fromApp), request))


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
        if path.startswith(dir_name) and not path.startswith("/"):
            path = f"/{path}"
        if path not in assets:
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
    paths = []
    if True:
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                paths.append(os.path.join(root, file))
        return paths
    else:
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
        if ext not in ['jpg', 'png', 'jpeg']:
            return False
        return ContentFile(base64.b64decode(imgstr), name=f"{uuid4().hex}.{ext}")
    except ValueError as e:
        return None
    except Exception as e:
        errorLog(e)
        return None


def base64ToFile(base64Data: base64) -> File:
    try:
        format, filestr = base64Data.split(';base64,')
        ext = format.split('/')[-1]
        return ContentFile(base64.b64decode(filestr), name=f"{uuid4().hex}.{ext}")
    except ValueError as e:
        return None
    except Exception as e:
        errorLog(e)
        return None


class JsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImageFieldFile):
            return str(obj)
        return super(JsonEncoder, self).default(obj)


def errorLog(*args, raiseErr=True):
    if not ISTESTING:
        logging.log(logging.ERROR, args)
        if ISDEVELOPMENT:
            return traceback.print_exc()


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
        return result['success'] if result['score'] > 0.7 else False
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
    path = path.split('?')[0].strip()
    path = path.split('#')[0].strip()
    for pathreg in settings.BYPASS_DEACTIVE_PATHS:
        if path == pathreg or testPathRegex(pathreg, path) or path.startswith(pathreg):
            return True
        elif path.strip('/') == pathreg.strip('/') or testPathRegex(pathreg.strip('/'), path.strip('/')) or path.strip('/').startswith(pathreg.strip('/')):
            return True
    return False


def sendUserNotification(users, payload: dict, ttl=1000):
    try:
        for user in users:
            send_user_notification(user, payload=payload, ttl=ttl)
        return True
    except Exception as e:
        errorLog(e)
        return False


def sendGroupNotification(groups, payload, ttl=1000):
    try:
        for group in groups:
            send_group_notification(group, payload=payload, ttl=ttl)
        return True
    except Exception as e:
        errorLog(e)
        return False


def user_device_notify(user_s, 
    title, body=None, url=None, icon=None,
    badge=None, actions=[],
    dir=None, image=None, lang=None, renotify=None, requireInteraction=False, silent=False, tag=None, timestamp=None, vibrate=None
):
    if not user_s:
        return False
    users = user_s
    if not isinstance(user_s, list):
        users = [user_s]
    return addMethodToAsyncQueue(f"main.methods.{sendUserNotification.__name__}", users, dict(
        title=title,
        body=body,
        url=url,
        icon=icon,
        badge=badge, actions=actions,dir=dir,image=image,lang=lang,renotify=renotify,requireInteraction=requireInteraction,
        silent=silent, tag=tag, timestamp=timestamp, vibrate=vibrate
    ))


def group_device_notify(group_s, title, body=None, url=None, icon=None,
    badge=None, actions=[],
    dir=None, image=None, lang=None, renotify=None, requireInteraction=False, silent=False, tag=None, timestamp=None, vibrate=None
):
    if not group_s or not len(group_s):
        return False
    groups = group_s
    if not isinstance(group_s, list):
        groups = [group_s]
    return addMethodToAsyncQueue(f"main.methods.{sendGroupNotification.__name__}", groups, dict(
        title=title,
        body=body,
        url=url,
        icon=icon,
        badge=badge, actions=actions,dir=dir,image=image,lang=lang,renotify=renotify,requireInteraction=requireInteraction,
        silent=silent, tag=tag, timestamp=timestamp, vibrate=vibrate
    ))


def addActivity(view, user, request_get, request_post, status):
    ActivityRecord.objects.create(view_name=view, user=user, request_get=json.dumps(
        request_get), request_post=json.dumps(request_post), response_status=status)


def activity(request, response):
    addMethodToAsyncQueue(f"main.methods.{addActivity.__name__}", request.path,
                          request.user, request.GET.__dict__, request.POST, response.status_code)


def removeUnverified():
    from people.models import Profile, User
    time = timezone.now() + timedelta(days=-4)
    users = EmailAddress.objects.filter(
        verified=False,
        primary=True,
        user__date_joined__lte=time
    ).values_list('user', flat=True)
    if not EmailAddress.objects.filter(user__id__in=list(users), verified=True).exists():
        profs = Profile.objects.filter(user__id__in=list(users)).delete()
        delusers = User.objects.filter(id__in=list(users)).delete()
        return delusers, profs
    return False

def htmlmin(htmlstr:str, *args, **kwargs):
    try:
        mincode = html_minify(htmlstr, *args, **kwargs)
        if len(re.findall(r'<(html|\/html|)>',htmlstr)) != 0:
            return mincode
        return re.sub(r'<(html|head|body|\/html|\/head|\/body)>', '', mincode)
    except:
        return htmlstr.strip()
