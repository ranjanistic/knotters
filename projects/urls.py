from django.urls import path
from main.views import landing
from .views import *

urlpatterns = [
    path('', allProjects),
    path('create/validate/<str:field>', validateField),
    path('create', create),
    path('submit', submitProject),
    path('landing', landing),
    path('profile/<str:reponame>', profile),
    path('projectinfo/<str:projectID>/<str:info>', projectInfo)
]
