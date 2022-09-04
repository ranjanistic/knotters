from django.contrib import admin
from django.urls import path
from howto.views import *
from main.strings import URL

urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Howto.CREATE, createArticle),
    path(URL.Howto.SAVE, saveArticle),
    path(URL.Howto.PUBLISH, publish),
    path(URL.Howto.VIEW, view),
    path(URL.Howto.SEARCH_TOPICS, topicsSearch),
    path(URL.Howto.EDIT_TOPICS, topicsUpdate),
    path(URL.Howto.SEARCH_TAGS, tagsSearch),
    path(URL.Howto.EDIT_TAGS, tagsUpdate),
    path(URL.Howto.DELETE, deleteArticle),
    path(URL.Howto.SECTION, section),
    path(URL.Howto.RATING, submitArticleRating),
    path(URL.Howto.TOGGLE_ADMIRATION, toggleAdmiration),
    path(URL.Howto.ADMIRATIONS, articleAdmirations),
]