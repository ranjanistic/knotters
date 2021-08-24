from django.urls import path
from main.strings import URL
from .views import *

urlpatterns = [
    path(URL.INDEX, index),
    path(URL.People.PROFILE, profile),
    path(URL.People.PROFILEEDIT, editProfile),
    path(URL.People.PROFILETAB, profileTab),
    path(URL.People.SETTINGTAB, settingTab),
    path(URL.People.ACCOUNTPREFERENCES, accountprefs),
    path(URL.People.TOPICSEARCH, topicsSearch),
    path(URL.People.TOPICSUPDATE, topicsUpdate),
    path(URL.People.ACCOUNTACTIVATION, accountActivation),
    path(URL.People.GETSUCCESSOR, getSuccessor),
    path(URL.People.INVITESUCCESSOR, profileSuccessor),
    path(URL.People.SUCCESSORINVITE, successorInvitation),
    path(URL.People.SUCCESSORINVITEACTION, successorInviteAction),
    path(URL.People.ACCOUNTDELETE, accountDelete),
    path(URL.People.ZOMBIE, zombieProfile),
    path(URL.People.GITHUB_EVENTS, githubEventsListener),
]
