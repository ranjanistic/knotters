from django.urls import path
from main.strings import URL
from .views import *

urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Projects.ALLLICENSES, allLicences),
    path(URL.Projects.LICENSE, licence),
    path(URL.Projects.LICENSES, licences),
    path(URL.Projects.ADDLICENSE, addLicense),
    path(URL.Projects.CREATEVALIDATEFIELD, validateField),
    path(URL.Projects.CREATE, create),
    path(URL.Projects.CREATE_FREE, createFree),
    path(URL.Projects.CREATE_MOD, createMod),
    path(URL.Projects.SUBMIT_FREE, submitFreeProject),
    path(URL.Projects.SUBMIT_MOD, submitProject),
    path(URL.Projects.TRASH, trashProject),
    path(URL.Projects.PROFILE_MOD, profileMod),
    path(URL.Projects.PROFILE_FREE, profileFree),
    path(URL.Projects.PROFILEEDIT, editProfile),
    path(URL.Projects.MANAGE_ASSETS, manageAssets),
    path(URL.Projects.TOPICSEARCH, topicsSearch),
    path(URL.Projects.TOPICSUPDATE, topicsUpdate),
    path(URL.Projects.TAGSEARCH, tagsSearch),
    path(URL.Projects.TAGSUPDATE, tagsUpdate),
    path(URL.Projects.LIVEDATA, liveData),
    path(URL.Projects.GITHUB_EVENTS, githubEventsListener),
    # path(URL.Projects.GITHUB_EVENTS_FREE, githubEventsListenerFree),
    path(URL.Projects.BROWSE_SEARCH, browseSearch),
]
