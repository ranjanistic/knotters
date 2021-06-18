from django.contrib import admin
from django.urls import path,include
from .views import *
from . import env
from django.conf.urls.static import static
from django.conf import settings
from .strings import PROJECTS, COMPETE, PEOPLE, MODERATION

urlpatterns = [
    path(env.ADMINPATH, admin.site.urls),
    path('', index),
    path('accounts/', include('allauth.urls')),
    path('projects/', include(f'{PROJECTS}.urls')),
    path('compete/', include(f'{COMPETE}.urls')),
    path('people/', include(f'{PEOPLE}.urls')),
    path('moderation/', include(f'{MODERATION}.urls')),
    path('redirector/', redirector),
    path('docs/', docIndex),
    path('docs/<str:type>', docs),
    path('landing', landing),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
