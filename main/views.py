from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from . import env
from django.contrib.auth.decorators import login_required


def renderData(data={}):
    data['appname'] = env.PUBNAME
    return data

@login_required
def index(request):
    return render(request,'index.html', renderData())


@login_required
def index2(request):
    return HttpResponse("hello")

    