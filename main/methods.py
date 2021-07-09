import base64
import os
from django.http.response import HttpResponse, JsonResponse
import requests
import re
from django.http.request import HttpRequest
from django.shortcuts import render
from django.core.files.base import ContentFile, File
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .env import ISPRODUCTION
from .settings import SENDER_API_URL_SUBS, SENDER_API_HEADERS, BASE_DIR


def renderData(data: dict = {}, fromApp: str = '') -> dict:
    """
    Adds default meta data to the dictionary 'data' which is assumed to be sent with a rendering template.

    :param: fromApp: The subapplication name from whose context this method will return udpated data.
    """
    data['ROOT'] = f"/{fromApp}"
    data['SUBAPPNAME'] = fromApp
    return data


def renderView(request: HttpRequest, view: str, data: dict = {}, fromApp: str = '') -> HttpResponse:
    """
    Returns text/html data as http response via given template view name.

    :view: The template view name (without extension), under the fromApp named folder
    :data: The dict data to be render in the view.
    :fromApp: The subapplication division name under which the given view named template file resides
    """
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
    })


def replaceUrlParamsWithStr(path: str, replacingChar: str = '*') -> str:
    """
    Replaces <str:param> of defined urls with given character (default: *), primarily for dynamic client side service worker.
    """
    return re.sub(r'(<str:)+[a-zA-Z0-9]+(>)', replacingChar, path)


def getDeepFilePaths(dir_name, appendWhen):
    """
    Returns list of mapping of file paths only inside the given directory.

    :appendWhen: a function, with argument as traversed path in loop, should return bool whether given arg path is to be included or not.
    """
    staticAssets = mapDeepPaths(os.path.join(BASE_DIR, f'{dir_name}/'))
    assets = []
    for stat in staticAssets:
        path = str(stat).replace(str(os.getcwd()+"\\"), '/')
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


def sendEmail(to: str, subject: str, html: str, body: str) -> bool:
    if ISPRODUCTION:
        try:
            msg = EmailMultiAlternatives(subject, body=body, to=[to])
            msg.attach_alternative(content=html, mimetype="text/html")
            msg.send()
            return True
        except:
            return False
    else:
        print(to, body)
        return True


def getEmailHtmlBody(greeting: str, header: str, footer: str, actions: list = [], conclusion: str = '') -> str and str:
    """
    Creates html and body content using parameters via the application's standard email template.

    :greeting: Top greeting to target
    :header: Beginnning text
    :footer: Ending text
    :actions: Actions { name, url } to be included in content
    :conclusion: Final short summary text

    :returns: html, body
    """
    data = {
        'greeting': greeting,
        'headertext': header,
        'footertext': footer,
        'current_site': {
            'name': 'Knotters',
            'domain': 'knotters.org'
        }
    }
    body = f"{greeting}\n\n{header}\n\n"
    if actions:
        data['actions'] = actions
        for action in actions:
            body = f"{body}{action['url']}\n"

    if conclusion:
        data['conclusion'] = conclusion
        body = f"{body}\n{conclusion}"

    html = render_to_string('account/email/email.html', data)
    return html, body


def sendAlertEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str) -> bool:
    html, body = getEmailHtmlBody(
        greeting=f"Hello {username}", header=header, footer=footer, conclusion=conclusion)
    return sendEmail(to=to, subject=subject, html=html, body=body)


def sendActionEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str = '', actions: list = []) -> bool:
    html, body = getEmailHtmlBody(
        greeting=f"Hello {username}", header=header, footer=footer, conclusion=conclusion, actions=actions)
    return sendEmail(to=to, subject=subject, html=html, body=body)
