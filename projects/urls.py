from django.urls import path
from main.strings import URL
from .views import *

urlpatterns = [
    path(URL.INDEX, allProjects),
    path(URL.Projects.LICENSE, licence),
    path(URL.Projects.LICENSES, licences),
    path(URL.Projects.CREATEVALIDATEFIELD, validateField),
    path(URL.Projects.CREATE, create),
    path(URL.Projects.SUBMIT, submitProject),
    path(URL.Projects.TRASH, trashProject),
    path(URL.Projects.PROFILE, profile),
    path(URL.Projects.PROFILEEDIT, editProfile),
]
