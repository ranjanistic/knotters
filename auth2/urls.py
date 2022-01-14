from django.urls import path
from main.strings import URL
from .views import *

urlpatterns = [
    path(URL.INDEX, auth_index),
    path(URL.Auth.NOTIF_ENABLED, notification_enabled),
    path(URL.Auth.TAB_SECTION, auth_index_tab)
]