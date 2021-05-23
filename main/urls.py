from django.contrib import admin
from django.urls import path,include
from .views import *
from . import env
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path(env.ADMINPATH, admin.site.urls),
    path('', index),
    path('accounts/', include('allauth.urls')),
    path('projects/', include('project.urls')),
    path('redirector/', redirector),
    path('docs/', docIndex),
    path('docs/<str:type>', docs)
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
