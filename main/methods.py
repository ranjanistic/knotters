from .env import PUBNAME, MAILUSER, SITE
from django.shortcuts import render

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
