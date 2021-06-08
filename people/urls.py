from django.urls import path

from .views import *

urlpatterns = [
    path('', index),
    path('profile/<str:userID>', profile),
    path('userinfo/<str:userID>/<str:section>', userInfo)
]
