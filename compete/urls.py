from django.urls import path
from main.views import landing
from main.strings import url
from .views import *

urlpatterns = [
    path(url.INDEX, index),
    path(url.LANDINGS, landing),
    path(url.LANDING, landing),
    path(url.Compete.INDEXTAB, indexTab),
    path(url.Compete.COMPETETABSECTION, competitionTab),
    path(url.Compete.COMPID, competition),
    path(url.Compete.PARTICIPATE, createSubmission),
    path(url.Compete.REMOVEMEMBER, removeMember),
    path(url.Compete.DATA, data),
    path(url.Compete.INVITE, invite),
    path(url.Compete.INVITEACTION, inviteAction),
    path(url.Compete.INVITATION, invitation),
    path('save/<str:compID>/<str:subID>', save),
    path('submit/<str:compID>/<str:subID>', finalSubmit),
]
