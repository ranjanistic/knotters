from django.urls import path
from main.strings import URL
from .views import *

urlpatterns = [
    path(URL.INDEX, auth_index),
]