from django.urls import path
from main.strings import URL

from .views import *

urlpatterns = [
    # home
    path(URL.INDEX, index),
    path(URL.Compete.BROWSE_SEARCH, browseSearch),
    path(URL.Compete.INDEXTAB, indexTab),
    # profile
    path(URL.Compete.COMPETETABSECTION, competitionTab),
    path(URL.Compete.COMPID, competition),
    path(URL.Compete.TOGGLE_ADMIRATION, toggleAdmiration),
    path(URL.Compete.ADMIRATIONS, competeAdmirations),
    path(URL.Compete.PARTICIPATE, createSubmission),
    path(URL.Compete.REMOVEMEMBER, removeMember),
    path(URL.Compete.DATA, data),
    path(URL.Compete.INVITE, invite),
    path(URL.Compete.INVITEACTION, inviteAction),
    path(URL.Compete.INVITATION, invitation),
    path(URL.Compete.SAVE, save),
    path(URL.Compete.SUBMIT, finalSubmit),
    # judge
    path(URL.Compete.SUBMITPOINTS, submitPoints),
    # manager
    path(URL.Compete.DECLARERESULTS, declareResults),
    path(URL.Compete.GENERATE_CERTS, generateCertificates),
    # participants
    path(URL.Compete.TOPIC_SCORES, getTopicScores),
    path(URL.Compete.CLAIMXP, claimXP),
    # certificates
    path(URL.Compete.CERT_INDEX, certificateIndex),
    path(URL.Compete.CERT_VERIFY, certificateVerify),
    path(URL.Compete.CERTIFICATE, certificate),
    path(URL.Compete.CERTDOWNLOAD, downloadCertificate),
    path(URL.Compete.APPR_CERTIFICATE, appCertificate),
    path(URL.Compete.APPR_CERTDOWNLOAD, appDownloadCertificate),
]
