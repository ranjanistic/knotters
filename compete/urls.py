from django.urls import path
from main.strings import URL
from .views import *

urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Compete.INDEXTAB, indexTab),
    path(URL.Compete.COMPETETABSECTION, competitionTab),
    path(URL.Compete.COMPID, competition),
    path(URL.Compete.PARTICIPATE, createSubmission),
    path(URL.Compete.REMOVEMEMBER, removeMember),
    path(URL.Compete.DATA, data),
    path(URL.Compete.INVITE, invite),
    path(URL.Compete.INVITEACTION, inviteAction),
    path(URL.Compete.INVITATION, invitation),
    path(URL.Compete.SAVE, save),
    path(URL.Compete.SUBMIT, finalSubmit),
    path(URL.Compete.SUBMITPOINTS, submitPoints),
    path(URL.Compete.DECLARERESULTS, declareResults),
    path(URL.Compete.CLAIMXP, claimXP),
    path(URL.Compete.CERTIFICATE, certificate),
    path(URL.Compete.CERTDOWNLOAD, downloadCertificate),
]
