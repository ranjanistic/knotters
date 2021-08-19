import os
import base64
from django.core.handlers.wsgi import WSGIRequest
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.base import ContentFile, File
from django.db.models.fields.files import ImageFieldFile
from django.http.response import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import redirect, render

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
                    
    URLS = dict(**URLS,Docs=url.docs.getURLSForClient(),Auth=url.auth.getURLSForClient())

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
        data = dict(**data,error=error)
    if message:
        data = dict(**data,message=message)

    return JsonResponse({
        'code': code,
        **data
    }, encoder=JsonEncoder)


def respondRedirect(fromApp: str = str(), path: str = str(), alert: str = str(), error: str = str()) -> HttpResponseRedirect:
    """
    returns redirect http response, with some parametric modifications.
    """
    return redirect(f"{url.getRoot(fromApp)}{path}{url.getMessageQuery(alert=alert,error=error,otherQueries=(path.__contains__('?') or path.__contains__('&')))}")


def getDeepFilePaths(dir_name, appendWhen):
    from .settings import BASE_DIR

    """
    Returns list of mapping of file paths only inside the given directory.

    :appendWhen: a function, with argument as traversed path in loop, should return bool whether given arg path is to be included or not.
    """
    allassets = mapDeepPaths(os.path.join(BASE_DIR, f'{dir_name}/'))
    assets = list()
    for asset in allassets:
        path = str(asset).replace(str(BASE_DIR), str())
        if path.startswith('\\'):
            path = str(path).strip("\\")
        if path.startswith(dir_name):
            path = f"/{path}"
        if appendWhen(path) and not assets.__contains__(path):
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
        return ContentFile(base64.b64decode(imgstr), name='profile.' + ext)
    except Exception as e:
        errorLog(e)
        return None


class JsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImageFieldFile):
            return str(obj)
        return super(JsonEncoder, self).default(obj)


def classAttrsToDict(className, appendCondition) -> dict:
    data = dict()
    for key in className.__dict__:
        if not (str(key).startswith('__') and str(key).endswith('__')):
            if appendCondition(key, className.__dict__.get(key)):
                data[key] = className.__dict__.get(key)
    return data


def errorLog(error):
    from .env import ISDEVELOPMENT, ISTESTING
    if not ISTESTING:
        file = open('_logs_/errors.txt', 'r')
        existing = file.read()
        file.close()
        file2 = open('_logs_/errors.txt', 'w')
        new = f"{existing}\n{timezone.now()}\n{error}"
        file2.write(new)
        file2.close()
        if ISDEVELOPMENT:
            print(error)


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

from .strings import url, MANAGEMENT, MODERATION, COMPETE, PROJECTS, PEOPLE, DOCS