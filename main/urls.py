from django.contrib import admin
from django.urls import path,include
from . import env
from .views import *
urlpatterns = [
    path(env.ADMINPATH, admin.site.urls),
    path('', index),
    path('party', index2),
    path('accounts/', include('allauth.urls'))
]