from django.contrib import admin
from django.urls import path,include
from . import env
from .views import *

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path(env.ADMINPATH, admin.site.urls),
    path('', index),
    path('accounts/', include('allauth.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)