from django.urls import path
from main.views import landing
from main.strings import url
from .views import *

urlpatterns = [
    path(url.INDEX, index),
    path(url.LANDING, landing),
    path(url.LANDINGS, landing),
    path(url.People.PROFILE, profile),
    path(url.People.PROFILEEDIT, editProfile),
    path(url.People.PROFILETAB, profileTab),
    path(url.People.SETTINGTAB, settingTab),
]
