from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .strings import URL, PROJECTS, COMPETE, PEOPLE, MODERATION, MANAGEMENT
from .env import ISPRODUCTION, ADMINPATH
from .views import *

urlpatterns = [
    path(URL.ROBOTS_TXT, Robots.as_view(), name=URL.ROBOTS_TXT),
    path(URL.MANIFEST, Manifest.as_view(), name=URL.MANIFEST),
    path(URL.SERVICE_WORKER, ServiceWorker.as_view(), name=URL.SERVICE_WORKER),
    path(ADMINPATH, admin.site.urls),
    path(URL.INDEX, index),
    path(URL.APPLANDING, applanding),
    path(URL.LANDING, landing),
    path(URL.OFFLINE, offline),
    path(URL.AUTH, include('allauth_2fa.urls')),
    path(URL.AUTH, include('allauth.urls')),
    path(URL.PROJECTS, include(f'{PROJECTS}.urls')),
    path(URL.COMPETE, include(f'{COMPETE}.urls')),
    path(URL.PEOPLE, include(f'{PEOPLE}.urls')),
    path(URL.MODERATION, include(f'{MODERATION}.urls')),
    path(URL.MANAGEMENT, include(f'{MANAGEMENT}.urls')),
    path(URL.REDIRECTOR, redirector),
    path(URL.DOCS, docIndex),
    path(URL.DOCTYPE, docs),
    path(URL.BROWSER, browser),
    path('email/<str:template>', mailtemplate)
]

if not ISPRODUCTION:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + \
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
