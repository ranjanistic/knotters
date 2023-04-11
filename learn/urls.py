from django.urls import path
from main.strings import URL
from learn.views import *
  

urlpatterns = [
    path(URL.INDEX, index),
    path('',courseactions),
    path('',lessonactions),
]
