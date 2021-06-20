from django.shortcuts import render
from django.core.files.base import ContentFile
import base64
from .env import PUBNAME, MAILUSER, SITE
from .strings import DIVISIONS


def renderData(data={},fromApp = ''):
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

def renderView(request, view, data={}, fromApp=''):
    return render(request, f"{'' if fromApp == '' else f'{fromApp}/' }{view}.html", renderData(data,fromApp))


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
