from django.urls import path
from main.strings import url
from .views import *

urlpatterns = [
    path(url.INDEX, allProjects),
    path(url.Projects.CREATEVALIDATEFIELD, validateField),
    path(url.Projects.CREATE, create),
    path(url.Projects.SUBMIT, submitProject),
    path(url.Projects.PROFILE, profile),
    path(url.Projects.PROFILEEDIT, editProfile),
    path(url.Projects.PROJECTINFO, projectInfo),
]
