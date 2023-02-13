from django.urls import path
from main.strings import URL

from .views import *

urlpatterns = [
    path(URL.Api.VERIFY_CREDENTIALS, verifyCredentials),
    path(URL.Api.REFRESH_TOKEN, refreshToken),
    path(URL.Api.USER, tokenUser),

]
