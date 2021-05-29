from django.urls import path

from .views import *

urlpatterns = [
    path('', allProjects),
    path('create', create),
    path('profile/<str:reponame>', profile)
]
