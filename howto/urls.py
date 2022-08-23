from django.contrib import admin
from django.urls import path
from howto.views import *
from main.strings import URL

urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Howto.CREATE, createArticle),
    path(URL.Howto.SAVE, saveArticle),
    path(URL.Howto.DRAFT, draft),
    path(URL.Howto.VIEW, view),
    path(URL.Howto.DELETE, deleteArticle),
]