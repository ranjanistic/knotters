from .env import PUBNAME
from django.shortcuts import render

def renderView(request, view, data={}):
    data['appname'] = PUBNAME
    return render(request, view, data)
