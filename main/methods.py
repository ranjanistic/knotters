from django.shortcuts import render
import re
from django.core.files.base import ContentFile
import base64
import requests
from .env import PUBNAME, MAILUSER, SITE, VERSION
from .settings import SENDER_API_URL_SUBS, SENDER_API_HEADERS
from .strings import DIVISIONS


def renderData(data={}, fromApp=''):
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
    data['VERSION'] = VERSION
    data['SUBAPPS'] = {}
    for div in DIVISIONS:
        data['SUBAPPS'][div] = div
    return data


def renderView(request, view, data={}, fromApp=''):
    return render(request, f"{'' if fromApp == '' else f'{fromApp}/' }{view}.html", renderData(data, fromApp))

def replaceUrlParamsWithStr(path:str,replacingChar:str='*')->str:
    return re.sub(r'(<str:)+[a-zA-Z0-9]+(>)', replacingChar, path)

def maxLengthInList(list=[]):
    max = len(str(list[0]))
    for item in list:
        if max < len(str(item)):
            max = len(str(item))
    return max


def base64ToImageFile(base64Data):
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


def getUserFromMailingServer(email: str, fullData=False) -> dict:
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
    subscriber = getUserFromMailingServer(email,True)
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
