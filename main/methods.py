import base64
import requests
from django.http.request import HttpRequest
from django.shortcuts import render
from django.core.files.base import ContentFile, File
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from .env import PUBNAME, MAILUSER, SITE
from .settings import SENDER_API_URL_SUBS, SENDER_API_HEADERS
from .strings import DIVISIONS


def renderData(data: dict = {}, fromApp: str = '') -> dict:
    """
    Adds default meta data to the dictionary 'data' which is assumed to be sent with a rendering template.

    :param: fromApp: The subapplication name from whose context this method will return udpated data.
    """
    data['APPNAME'] = PUBNAME
    data['CONTACTMAIL'] = MAILUSER
    data['DESCRIPTION'] = "Solving problems together."
    data['SUBAPPNAME'] = fromApp
    data['ROOT'] = f"/{fromApp}"
    data['SITE'] = SITE
    data['SUBAPPS'] = {}
    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
    return data


def renderView(request: HttpRequest, view: str, data: dict = {}, fromApp: str = ''):
    return render(request, f"{'' if fromApp == '' else f'{fromApp}/' }{view}.html", renderData(data, fromApp))


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
    response = requests.request(
        'POST', SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
    return response['success']


def getUserFromMailingServer(email: str, fullData: bool = False) -> dict:
    """
    Returns user data from mailing server.

    :fullData: If True, returns only the id of user from mailing server. Default: False
    """
    if not email:
        return None
    response = requests.request(
        'GET', f"{SENDER_API_URL_SUBS}/by_email/{email}", headers=SENDER_API_HEADERS).json()
    return response['data'] if fullData else response['data']['id']


def removeUserFromMailingServer(email: str) -> bool:
    """
    Removes user from mailing server.
    """
    subscriber = getUserFromMailingServer(email, True)
    if not subscriber:
        return False

    payload = {
        "subscribers": [subscriber['id']]
    }
    response = requests.request(
        'DELETE', SENDER_API_URL_SUBS, headers=SENDER_API_HEADERS, json=payload).json()
    return response['success']


def addUserToMailingGroup(email: str, groupID: str) -> bool:
    """
    Adds user to a mailing group (assuming the user to be an existing server subscriber).
    """
    subID = getUserFromMailingServer(email)
    if not subID:
        return False
    payload = {
        "subscribers": [subID],
    }
    response = requests.request(
        'POST', f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()
    return response['success']


def removeUserFromMailingGroup(groupID: str, email: str) -> bool:
    """
    Removes user from a mailing group.
    """

    subID = getUserFromMailingServer(email=email)
    if not subID:
        return False
    payload = {
        "subscribers": [subID]
    }
    response = requests.request(
        'DELETE', f"{SENDER_API_URL_SUBS}/groups/{groupID}", headers=SENDER_API_HEADERS, json=payload).json()
    return response['success']


def getEmailHtmlBody(greeting: str, header: str, footer: str, actions: list = [], conclusion: str = '') -> str and str:
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


def sendAlertEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str):
    html, body = getEmailHtmlBody(
        greeting=f"Hello {username}", header=header, footer=footer, conclusion=conclusion)
    msg = EmailMultiAlternatives(subject, body=body, to=[to])
    msg.attach_alternative(content=html, mimetype="text/html")
    msg.send()


def sendActionEmail(to: str, username: str, subject: str, header: str, footer: str, conclusion: str = '', actions: list = []):
    print('yess')
    html, body = getEmailHtmlBody(
        greeting=f"Hello {username}", header=header, footer=footer, conclusion=conclusion, actions=actions)
    msg = EmailMultiAlternatives(subject, body=body, to=[to])
    msg.attach_alternative(content=html, mimetype="text/html")
    msg.send()

