import base64
import os
import requests
import re
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.base import ContentFile, File
from django.db.models.fields.files import ImageFieldFile
from django.http.response import HttpResponse, JsonResponse
from django.http.request import HttpRequest
from django.shortcuts import redirect, render
from .strings import URL, url
from .settings import SENDER_API_URL_SUBS, SENDER_API_HEADERS, BASE_DIR


def renderData(data: dict = {}, fromApp: str = '') -> dict:
    """
    Adds default meta data to the dictionary 'data' which is assumed to be sent with a rendering template.

    :param: fromApp: The subapplication name from whose context this method will return udpated data.
    """
    data['ROOT'] = url.getRoot(fromApp)
    data['SUBAPPNAME'] = fromApp
    return data


def renderView(request: HttpRequest, view: str, data: dict = {}, fromApp: str = '') -> HttpResponse:
    """
    Returns text/html data as http response via given template view name.

    :view: The template view name (without extension), under the fromApp named folder
    :data: The dict data to be render in the view.
    :fromApp: The subapplication division name under which the given view named template file resides
    """
    data['URLS'] = data.get('URLS',{})

    def cond(key,value):
        return str(key).isupper()
    urls = classAttrsToDict(URL,cond)
    
    for key in urls:
        data['URLS'][key] = f"{url.getRoot() if urls[key] != URL.ROOT else ''}{replaceUrlParamsWithStr(str(urls[key]))}"

    return render(request, f"{'' if fromApp == '' else f'{fromApp}/' }{view}.html", renderData(data, fromApp))


def respondJson(code: str, data: dict = {}, error: str = '', message: str = '') -> JsonResponse:
    """
    Returns application/json data as http response.

    :code: A code name, indicating response type.
    :data: The dict data to be sent along with code.
    """
    return JsonResponse({
        'code': code,
        'error': error,
        'message': message,
        **data
    }, encoder=JsonEncoder)


def respondRedirect(fromApp: str = '', path: str = '', alert: str = '', error: str = ''):
    """
    returns redirect http response, with some parametric modifications.
    """
    return redirect(f"{url.getRoot(fromApp)}{path}{url.getMessageQuery(alert,error)}")


def replaceUrlParamsWithStr(path: str, replacingChar: str = '*') -> str:
    """
    Replaces <str:param> of defined urls with given character (default: *), primarily for dynamic client side service worker.
    """
    return re.sub(r'(<str:|<int:)+[a-zA-Z0-9]+(>)', replacingChar, path)


def getDeepFilePaths(dir_name, appendWhen):
    """
    Returns list of mapping of file paths only inside the given directory.

    :appendWhen: a function, with argument as traversed path in loop, should return bool whether given arg path is to be included or not.
    """
    staticAssets = mapDeepPaths(os.path.join(BASE_DIR, f'{dir_name}/'))
    assets = []
    for stat in staticAssets:
        path = str(stat).replace(str(BASE_DIR), '')
        if path.startswith('\\'):
            path = str(path).strip("\\")
        if path.startswith(dir_name):
            path = f"/{path}"
        if appendWhen(path) and not assets.__contains__(path):
            assets.append(path)

    return assets


def mapDeepPaths(dir_name, traversed=[], results=[]):
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

    paths = []
    for file_name, _ in results:
        paths.append(str(file_name).strip('.'))
    return paths


def maxLengthInList(list: list = []) -> int:
    max = len(str(list[0]))
    for item in list:
        if max < len(str(item)):
            max = len(str(item))
    return max


def base64ToImageFile(base64Data: base64) -> File:
    try:
        format, imgstr = base64Data.split(';base64,')
        ext = format.split('/')[-1]
        if not ['jpg', 'png', 'jpeg'].__contains__(ext):
            return False
        return ContentFile(base64.b64decode(imgstr), name='profile.' + ext)
    except:
        return None


class JsonEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, ImageFieldFile):
            return str(obj)
        return super(JsonEncoder, self).default(obj)



def classAttrsToDict(className, appendCondition)->dict:
    data = {}
    for key in className.__dict__:
        if not (str(key).startswith('__') and str(key).endswith('__')):
            if appendCondition(key,className.__dict__.get(key)):
                data[key] = className.__dict__.get(key)
    return data

def addUserToMailingServer(email: str, first_name: str, last_name: str) -> bool:
    """
    Adds a user (assuming to be new) to mailing server.
    By default, also adds the subscriber to the default group.
    """
    payload = {
        "email": email,
        "firstname": first_name,
        "lastname": last_name,
        "groups": ["dL8pBD"],
    }
    try:
        response = requests.request(
            'POST', SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
        return response['success']
    except:
        return False


def getUserFromMailingServer(email: str, fullData: bool = False) -> dict:
    """
    Returns user data from mailing server.

    :fullData: If True, returns only the id of user from mailing server. Default: False
    """
    try:
        if not email:
            return None
        response = requests.request(
            'GET', f"{SENDER_API_URL_SUBS}/by_email/{email}", headers=SENDER_API_HEADERS).json()
        return response['data'] if fullData else response['data']['id']
    except:
        return None


def removeUserFromMailingServer(email: str) -> bool:
    """
    Removes user from mailing server.
    """
    try:
        subscriber = getUserFromMailingServer(email, True)
        if not subscriber:
            return False

        payload = {
            "subscribers": [subscriber['id']]
        }
        response = requests.request(
            'DELETE', SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
        return response['success']
    except:
        return None


def addUserToMailingGroup(email: str, groupID: str) -> bool:
    """
    Adds user to a mailing group (assuming the user to be an existing server subscriber).
    """
    try:
        subID = getUserFromMailingServer(email)
        if not subID:
            return False
        payload = {
            "subscribers": [subID],
        }
        response = requests.request(
            'POST', f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()

        return response['success']
    except:
        return None


def removeUserFromMailingGroup(groupID: str, email: str) -> bool:
    """
    Removes user from a mailing group.
    """
    try:
        subID = getUserFromMailingServer(email=email)
        if not subID:
            return False
        payload = {
            "subscribers": [subID]
        }
        response = requests.request(
            'DELETE', f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()
        return response['success']
    except:
        return None
