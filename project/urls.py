from django.urls import path
from django.conf.urls.static import static
from django.conf import settings

from .views import *

urlpatterns = [
    path('', allProjects),
    path('create', create),
    path('profile/<str:id>', profile)
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
