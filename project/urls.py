from django.urls import path

from .views import *

urlpatterns = [
    path('', allProjects),
    path('create', create),
    path('submit', submitProject),
    path('profile/<str:reponame>', profile)
]
