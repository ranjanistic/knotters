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
]
