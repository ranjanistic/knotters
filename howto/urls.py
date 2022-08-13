from django.contrib import admin
from django.urls import path
from howto import views

urlpatterns = [
    path("", views.index),
    path("<str:nickname>", views.article)
]