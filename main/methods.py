from .env import PUBNAME, MAILUSER, SITE
from django.shortcuts import render
from django.core.files.base import ContentFile
import base64

def renderView(request, view, data={}):
    data['appname'] = PUBNAME
    data['contactmail'] = MAILUSER
    data['description'] = "Solving problems together."
    data['site'] = SITE
    return render(request, view, data)

def maxLengthInList(list=[]):
    max = len(str(list[0]))
    for item in list:
        if max< len(str(item)):
            max = len(str(item))
    return max

def base64ToImageFile(base64Data):
    try:
        format, imgstr = base64Data.split(';base64,') 
        ext = format.split('/')[-1] 
        return ContentFile(base64.b64decode(imgstr), name='profile.' + ext)
    except:
        return None