from django.contrib import admin
from django.urls import path, include
from .views import *
from . import env
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.conf import settings
from .strings import PROJECTS, COMPETE, PEOPLE, MODERATION, url

urlpatterns = [
    path(env.ADMINPATH, admin.site.urls),
    path(url.INDEX, index),
    path('service-worker.js', (TemplateView.as_view(
        template_name="service-worker.js",
        content_type='application/javascript',
    )), name='service-worker.js'),
    path('offline', offline),
    path(url.ACCOUNTS, include('allauth.urls')),
    path(url.PROJECTS, include(f'{PROJECTS}.urls')),
    path(url.COMPETE, include(f'{COMPETE}.urls')),
    path(url.PEOPLE, include(f'{PEOPLE}.urls')),
    path(url.MODERATION, include(f'{MODERATION}.urls')),
    path(url.REDIRECTOR, redirector),
    path(url.DOCS, docIndex),
    path(url.DOCTYPE, docs),
    path(url.LANDINGS, landing),
    path(url.LANDING, landing),
    path(url.LANDING, landing),
    path('email/<str:template>', mailtemplate)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
