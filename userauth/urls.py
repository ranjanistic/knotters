from django.contrib import admin
from django.urls import path,include
from main import env
from .views import *

urlpatterns = [
    path('getuser', getCurrentUser)
]