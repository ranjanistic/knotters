from base64 import b64decode
from datetime import timedelta
from json import dumps as json_dumps
from logging import ERROR as LOG_CODE_ERROR
from logging import log
from mimetypes import guess_extension, guess_type
from os import path as ospath
from os import walk as oswalk
from re import compile as re_compile
from re import findall as re_findall
from re import sub as re_sub
from traceback import print_exc
from uuid import uuid4

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.handlers.wsgi import WSGIRequest
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.fields.files import ImageFieldFile
from django.http.response import (HttpResponse, HttpResponseRedirect,
                                  JsonResponse)
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django_q.tasks import async_task
from htmlmin.minify import html_minify
from management.models import ActivityRecord
from requests import post as postRequest
from webpush import send_group_notification, send_user_notification

from .env import ASYNC_CLUSTER, ISDEVELOPMENT, ISPRODUCTION, ISTESTING
from .strings import (AUTH, AUTH2, COMPETE, DOCS, MANAGEMENT, MODERATION,
                      PEOPLE, PROJECTS, Code, url)


def renderData(data: dict = dict(), fromApp: str = str()) -> dict:
    """Returns default context data for the given subapplication.

    Args:
        data (dict, optional): The additional dict data in context. Defaults to dict().
        fromApp (str, optional): The subapplication division name under which the context data is generated. Defaults to str().

    Returns:
        dict: The default context data for the given subapplication.
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

    return dict(**data, URLS=URLS, ROOT=url.getRoot(fromApp), SUBAPPNAME=fromApp, DEBUG=settings.DEBUG)


def renderView(request: WSGIRequest, view: str, data: dict = dict(), fromApp: str = str()) -> HttpResponse:
    """Returns text/html http response via given template view name under fromApp subapplication, with default context data.

    Args:
        request (WSGIRequest): The request object.
        view (str): The template view name (without extension), under the fromApp named folder
        data (dict, optional): The dict data to be render in the view. Defaults to dict().
        fromApp (str, optional): The subapplication division name under which the given view named template file resides. Defaults to str().

    Returns:
        HttpResponse: The rendered text/html view as http response.
    """

    return render(request, f"{str() if fromApp == str() else f'{fromApp}/' }{view}.html", renderData(data, fromApp))


def renderString(request: WSGIRequest, view: str, data: dict = dict(), fromApp: str = str()) -> str:
    """Returns text/html data as string via given template view name under fromApp subapplication, with default context data.

    Args:
        request (WSGIRequest): The request object.
        view (str): The template view name (without extension), under the fromApp named folder
        data (dict, optional): The dict data to be render in the view. Defaults to dict().
        fromApp (str, optional): The subapplication division name under which the given view named template file resides. Defaults to str().

    Returns:
        str: The rendered text/html view as string.
    """
    return htmlmin(render_to_string(f"{str() if fromApp == str() else f'{fromApp}/' }{view}.html", renderData(data, fromApp), request))


def respondJson(code: str, data: dict = dict(), error: str = str(), message: str = str(), success: str = str()) -> JsonResponse:
    """returns json http response, with custom data.

    Args:
        code (str): The response code. [main.strings.Code.OK, main.strings.Code.NO]
        data (dict, optional): The data to be sent along with the response. Defaults to dict().
        error (str, optional): The error message to be sent along with the response. Defaults to str().
        message (str, optional): The message to be sent along with the response. Defaults to str().
        success (str, optional): The success message to be sent along with the response. Defaults to str().

    Returns:
        JsonResponse: The json http response.
    """

    if error:
        data = dict(**data, error=error)
    if message:
        data = dict(**data, message=message)
    if success:
        data = dict(**data, success=success)

    return JsonResponse(dict(
        code=code,
        **data
    ), encoder=JsonEncoder)


def respondRedirect(fromApp: str = str(), path: str = str(), alert: str = str(), error: str = str()) -> HttpResponseRedirect:
    """returns redirect http response, with some parametric modifications.

    Args:
        fromApp (str, optional): The subapplication division name under which the given path resides.
        path (str, optional): The path to redirect to.
        alert (str, optional): The alert message to be sent along with the redirect.
        error (str, optional): The error message to be sent along with the redirect.

    Returns:
        HttpResponseRedirect: The redirect http response.
    """
    return redirect(f"{url.getRoot(fromApp)}{path}{url.getMessageQuery(alert=alert,error=error,otherQueries=(path.__contains__('?') or path.__contains__('&')))}")


def getDeepFilePaths(dir_name: str, appendWhen: callable = None):
    """Returns list of mapping of file paths only inside the given directory.

    :appendWhen: 

    Args:
        dir_name (str): The directory name to be searched.
        appendWhen (callable, optional): a function, with argument as traversed path in loop, should return bool whether given arg path is to be included or not.

    Returns:
        list: list of mapping of file paths only inside the given directory.
    """
    allassets = mapDeepPaths(ospath.join(settings.BASE_DIR, f'{dir_name}/'))
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


def mapDeepPaths(dir_path: str) -> list:
    """Returns list of absolute file paths of all files inside the given directory.

    Args:
        dir_path (str): The directory path to be traversed.

    Returns:
        list<str>: List of absolute file paths of all files inside the given directory.
    """
    paths = []
    for root, _, files in oswalk(dir_path):
        for file in files:
            paths.append(ospath.join(root, file))
    return paths


def maxLengthInList(list: list = list()) -> int:
    """Returns the maximum length of str items in the list.

    Args:
        list (list<str>): list of str items. Defaults to [].

    Returns:
        int: maximum length of str items in the list.
    """
    max = len(str(list[0]))
    for item in list:
        if max < len(str(item)):
            max = len(str(item))
    return max


def minLengthInList(list: list = []) -> int:
    """Returns the minimum length of str items in the list.

    Args:
        list (list<str>): list of str items. Defaults to [].

    Returns:
        int: minimum length of str items in the list.
    """
    min = len(str(list[0]))
    for item in list:
        if min > len(str(item)):
            min = len(str(item))
    return min


def base64ToImageFile(base64Data) -> File:
    """Converts base64 data to file object, particularly for image file.

    Args:
        base64Data (str): base64 data of file
        filename (str, optional): actual filename of the file

    Returns:
        File: file object
        bool: False if file is not valid image file [png, jpg, jpeg]
        None: if base64 data is not valid or exception occurs
    """
    try:
        format, imgstr = base64Data.split(';base64,')
        ext = format.split('/')[-1]
        if ext not in ['jpg', 'png', 'jpeg']:
            return False
        return ContentFile(b64decode(imgstr), name=f"{uuid4().hex}.{ext}")
    except ValueError as e:
        return None
    except Exception as e:
        errorLog(e)
        return None


def base64ToFile(base64Data: str, filename=None) -> File:
    """Converts base64 data to file object.

    Args:
        base64Data (str): base64 data of file
        filename (str, optional): actual filename of the file

    Returns:
        File: file object
        None: if base64 data is not valid or exception occurs
    """
    try:
        format, filestr = base64Data.split(';base64,')
        if filename:
            ext = filename.split('.')[-1]
        else:
            ext = guess_extension(guess_type(base64Data)[0])
            if not ext:
                ext = format.split('/')[-1]
                if ext.startswith('x-zip'):
                    ext = "zip"
        return ContentFile(b64decode(filestr), name=f"{uuid4().hex}.{ext}")
    except ValueError as e:
        return None
    except Exception as e:
        errorLog(e)
        return None


class JsonEncoder(DjangoJSONEncoder):
    """A custom JSON encoder based on DjangoJSONEncoder.
    """

    def default(self, obj):
        if isinstance(obj, ImageFieldFile):
            return str(obj)
        return super(JsonEncoder, self).default(obj)


def errorLog(*args):
    """Logs error to console/file and emails error to admin, depending upon environment and logging settings.
    """
    if not ISTESTING:
        log(LOG_CODE_ERROR, args)
        if ISPRODUCTION:
            return addMethodToAsyncQueue(f"main.mailers.sendErrorLog", *args)
        if ISDEVELOPMENT:
            return print_exc()


def getNumberSuffix(value: int, withNumber=False) -> str:
    """Returns the suffix for the given number.

    Args:
        value (int): The number to get suffix for.
        withNumber (bool): Whether to return the number with suffix or not. Default is False.

    Returns:
        str: The suffix for the given number.
    """
    valuestr = str(value)
    if value == 1:
        return 'st' if not withNumber else f'{value}st'
    elif value == 2:
        return 'nd' if not withNumber else f'{value}nd'
    elif value == 3:
        return 'rd' if not withNumber else f'{value}rd'
    else:
        if value > 9:
            if valuestr[len(valuestr) - 2] == "1" or valuestr[len(valuestr) - 1] == "0":
                return "th" if not withNumber else f'{value}th'
            return getNumberSuffix(value=int(valuestr[len(valuestr) - 1]), withNumber=withNumber)
        else:
            return "th" if not withNumber else f'{value}th'


def verify_captcha(recaptcha_response: str) -> bool:
    """To verify google recaptcha response

    Args:
        recaptcha_response (str): recaptcha response received from client.

    Returns:
        bool: True if valid recaptcha response (not a bot) else False
    """
    try:
        resp = postRequest(settings.GOOGLE_RECAPTCHA_API_VERIFY_SITE, dict(
            secret=settings.GOOGLE_RECAPTCHA_SECRET,
            response=recaptcha_response
        ))
        result = resp.json()
        return result['success'] if result['score'] > 0.7 else False
    except Exception as e:
        errorLog(e)
        return False


def addMethodToAsyncQueue(methodpath, *params) -> str:
    """Adds method to task queue for cluster execution.

    Args:
        methodpath: The path of the method to be executed.

    Returns:
        str: The task id of the task added to the queue.
        bool: False if exception occurred.
    """
    try:
        if ASYNC_CLUSTER:
            return async_task(methodpath, *params)
        return True
    except Exception as e:
        errorLog(e)
        return False


def testPathRegex(parampath: str, path: str) -> bool:
    """Tests if given path matches the params based url path.

    Args:
        parampath (str): The params based (main.strings.Code.URLPARAM) url path to be used to check the given path.
        path (str): The path to be tested

    Returns:
        bool: True if path matches the params based url path.
    """
    localParamRegex = "[a-zA-Z0-9\. \\-\_\%]"
    regpath = re_sub(Code.URLPARAM, f"+{localParamRegex}+", parampath)
    if regpath == path:
        return True
    parts = regpath.split("+")
    if not parts[-1]:
        parts.pop()

    def eachpart(part: str):
        return localParamRegex if part == localParamRegex else f"({part})"
    finalreg = "^" + "+".join(map(eachpart, parts)) + "+$"
    match = re_compile(finalreg).match(path)
    if match:
        return len(match.groups()) > 0
    return False


def allowBypassDeactivated(path: str) -> bool:
    """To check if the path is allowed to be requested by a deactivated user

    Args:
        path (str): The path to be checked

    Returns:
        bool: True if the path is allowed to be requested by a deactivated user
    """
    path = path.split('#')[0].strip()
    path = path.split('?')[0].strip()
    for pathreg in settings.BYPASS_DEACTIVE_PATHS:
        if path == pathreg or testPathRegex(pathreg, path) or path.startswith(pathreg):
            return True
        elif path.strip('/') == pathreg.strip('/') or testPathRegex(pathreg.strip('/'), path.strip('/')) or path.strip('/').startswith(pathreg.strip('/')):
            return True
    return False


def sendUserNotification(users: list, payload: dict, ttl=1000):
    """To send device push notification to users.

    Args:
        groups (list<User>): List of user instances
        payload (dict): Notification payload data
        ttl (int, optional): Time to live in milliseconds. Defaults to 1000.

    Returns:
        bool: True if success, False otherwise.
    """
    try:
        for user in users:
            send_user_notification(user, payload=payload, ttl=ttl)
        return True
    except Exception as e:
        errorLog(e)
        return False


def sendGroupNotification(groups: list, payload: dict, ttl: int = 1000):
    """To send device push notification to subscription groups.

    Args:
        groups (list<str>): List of group names.
        payload (dict): Notification payload data
        ttl (int, optional): Time to live in milliseconds. Defaults to 1000.

    Returns:
        bool: True if success, False otherwise.
    """
    try:
        for group in groups:
            send_group_notification(group, payload=payload, ttl=ttl)
        return True
    except Exception as e:
        errorLog(e)
        return False


def user_device_notify(user_s: str,
                       title: str, body: str = None, url: str = None, icon: str = None,
                       badge: str = None, actions: list = [],
                       dir: str = None, image: str = None, lang: str = None, renotify: bool = None, requireInteraction: bool = False, silent: bool = False, tag: str = None, timestamp=None, vibrate: list = None
                       ):
    """Add queue task to send device push notification to a subscription group.

    Args:
        user_s (User, list<User>): The user instance or list of instances to send to.
        title (str): The notification title.
        body (str, optional): The notification body. Defaults to None.
        url (str, optional): The notification url. Defaults to None.
        icon (str, optional):  The notification icon url. Defaults to None.
        badge (str, optional): The notification badge url. Defaults to None.
        actions (list, optional): The notification actions. Defaults to [].
        dir (str, optional): The notification direction. Defaults to None.
        image (str, optional): The notification image url. Defaults to None.
        lang (str, optional): The notification language. Defaults to None.
        renotify (bool, optional): Whether to renotify. Defaults to None.
        requireInteraction (bool, optional): Whether the notification requires interaction. Defaults to False.
        silent (bool, optional): Whether the notification is silent. Defaults to False.
        tag (str, optional): The notification tag. Defaults to None.
        timestamp (int, optional): The notification timestamp. Defaults to None.
        vibrate (list, optional): The notification vibration levels list. Defaults to None.

    Returns:
        str: Task ID if successfully queued
        bool: False if failed
    """
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
        badge=badge, actions=actions, dir=dir, image=image, lang=lang, renotify=renotify, requireInteraction=requireInteraction,
        silent=silent, tag=tag, timestamp=timestamp, vibrate=vibrate
    ))


def group_device_notify(group_s: str, title: str, body: str = None, url: str = None, icon: str = None,
                        badge: str = None, actions: list = [],
                        dir: str = None, image: str = None, lang: str = None, renotify: bool = None, requireInteraction: bool = False, silent: bool = False, tag: str = None, timestamp=None, vibrate: list = None
                        ):
    """Add queue task to send device push notification to a subscription group.

    Args:
        group_s (str, list): The subscription group name or list of names to send to.
        title (str): The notification title.
        body (str, optional): The notification body. Defaults to None.
        url (str, optional): The notification url. Defaults to None.
        icon (str, optional):  The notification icon url. Defaults to None.
        badge (str, optional): The notification badge url. Defaults to None.
        actions (list, optional): The notification actions. Defaults to [].
        dir (str, optional): The notification direction. Defaults to None.
        image (str, optional): The notification image url. Defaults to None.
        lang (str, optional): The notification language. Defaults to None.
        renotify (bool, optional): Whether to renotify. Defaults to None.
        requireInteraction (bool, optional): Whether the notification requires interaction. Defaults to False.
        silent (bool, optional): Whether the notification is silent. Defaults to False.
        tag (str, optional): The notification tag. Defaults to None.
        timestamp (int, optional): The notification timestamp. Defaults to None.
        vibrate (list, optional): The notification vibration levels list. Defaults to None.

    Returns:
        str: Task ID if successfully queued
        bool: False if failed
    """
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
        badge=badge, actions=actions, dir=dir, image=image, lang=lang, renotify=renotify, requireInteraction=requireInteraction,
        silent=silent, tag=tag, timestamp=timestamp, vibrate=vibrate
    ))


def addActivity(view, user, request_get, request_post, status):
    ActivityRecord.objects.create(view_name=view, user=user, request_get=json_dumps(
        request_get), request_post=json_dumps(request_post), response_status=status)


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


def htmlmin(htmlstr: str, *args, **kwargs) -> str:
    """Minifies string based html code.
        If htmlstr does not contain <html> tags, then <head> and <body> tags will be removed, 
        presuming the htmlstr to be a component of an html page.

    Args:
        htmlstr (str): String based html code.

    Returns:
        str: Minified string based html code.
    """
    try:
        mincode = html_minify(htmlstr, *args, **kwargs)
        if len(re_findall(r'<(html|\/html|)>', htmlstr)) != 0:
            return mincode
        return re_sub(r'<(html|head|body|\/html|\/head|\/body)>', '', mincode)
    except:
        return htmlstr.strip()


def human_readable_size(num: float, suffix="B") -> str:
    """Converts a number to human readable memory size format.

    Args:
        num (float): Number to convert.
        suffix (str, optional): Suffix to append to the number. Defaults to "B".

    Returns:
        str: Human readable memory size format.
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"
