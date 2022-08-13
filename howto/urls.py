from django.contrib import admin
from django.urls import path
from howto import views

urlpatterns = [
    path("", views.howto),
    path("article/<slug:slug>/", views.article)
]