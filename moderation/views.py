from django.http.response import Http404, HttpResponse
from main.renderer import renderView
from project import *
from compete import *
from people import *

DIVISIONS = ['people','project','competition']

def moderation(request,division,id):
    if not DIVISIONS.__contains__(division):
        raise Http404()
    else:
        return HttpResponse(f"{division} moderation for {id}")
