from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from .views import ServiceWorker, Robots, Manifest,redirector, docIndex, docs, landing, offline, index, mailtemplate, applanding
from .strings import PROJECTS, COMPETE, PEOPLE, MODERATION, url
from . import env

urlpatterns = [
    path(url.ROBOTS_TXT, Robots.as_view(), name=url.ROBOTS_TXT),
    path(url.MANIFEST, Manifest.as_view(), name=url.MANIFEST),
    path(url.SERVICE_WORKER, ServiceWorker.as_view(), name=url.SERVICE_WORKER),
    path(env.ADMINPATH, admin.site.urls),
    path(url.INDEX, index),
    path(url.APPLANDING, applanding),
    path(url.LANDING, landing),
    path(url.OFFLINE, offline),
    path(url.ACCOUNTS, include('allauth_2fa.urls')),
    path(url.ACCOUNTS, include('allauth.urls')),
    path(url.PROJECTS, include(f'{PROJECTS}.urls')),
    path(url.COMPETE, include(f'{COMPETE}.urls')),
    path(url.PEOPLE, include(f'{PEOPLE}.urls')),
    path(url.MODERATION, include(f'{MODERATION}.urls')),
    path(url.REDIRECTOR, redirector),
    path(url.DOCS, docIndex),
    path(url.DOCTYPE, docs),
    path('email/<str:template>', mailtemplate)
]

if not env.ISPRODUCTION:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
