from django.urls import path
from main.strings import URL
from learn.views import *
from .views import *
from django.urls import include

urlpatterns = [
    path('', status),
    path('status/', status),
    path(URL.LEARN, include('learn.urls')),
    path(URL.Api.VERIFY_CREDENTIALS, verifyCredentials),
    path(URL.Api.REFRESH_TOKEN, refreshToken),
    path(URL.Api.USER, tokenUser),
]
