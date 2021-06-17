from django.urls import path

from .views import *

urlpatterns = [
    path('', allProjects),
    path('create/validate/<str:field>', validateField),
    path('create', create),
    path('submit', submitProject),
    path('profile/<str:reponame>', profile),
    path('projectinfo/<str:projectID>/<str:info>', projectInfo)
]
