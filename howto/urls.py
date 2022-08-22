from django.contrib import admin
from django.urls import path
from howto.views import *
from main.strings import URL

urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Howto.DRAFT, draft),
    # path(URL.HOWto.SECTION, section)
]