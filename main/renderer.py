from .env import PUBNAME, MAILUSER, SITE
from django.shortcuts import render

def renderView(request, view, data={}):
    data['appname'] = PUBNAME
    data['contactmail'] = MAILUSER
    data['description'] = "Solving problems together."
    data['site'] = SITE
    return render(request, view, data)
