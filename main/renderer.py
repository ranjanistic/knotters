from .env import PUBNAME, MAILUSER
from django.shortcuts import render

def renderView(request, view, data={}):
    data['appname'] = PUBNAME
    data['contactmail'] = MAILUSER
    return render(request, view, data)
