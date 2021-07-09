from django.urls import path
from main.strings import url
from .views import *

urlpatterns = [
    path(url.INDEX, index),
    path(url.People.PROFILE, profile),
    path(url.People.PROFILEEDIT, editProfile),
    path(url.People.PROFILETAB, profileTab),
    path(url.People.SETTINGTAB, settingTab),
    path(url.People.ACCOUNTPREFERENCES, accountprefs),
    path(url.People.ACCOUNTACTIVATION, accountActivation),
    path(url.People.ACCOUNTDELETE, accountDelete),
    path(url.People.INVITESUCCESSOR, profileSuccessor),
    path(url.People.SUCCESSORINVITE, successorInvitation),
    path(url.People.SUCCESSORINVITEACTION, successorInviteAction),
]
