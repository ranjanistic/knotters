from django.shortcuts import render
from . import env

def renderData(data={}):
    data['appname'] = env.PUBNAME
    return data

def index(request):
    return render(request,'index.html', renderData())