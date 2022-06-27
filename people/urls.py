from django.urls import path
from main.strings import URL

from .views import *

urlpatterns = [
    path(URL.INDEX, index),
    # profile
    path(URL.People.PROFILE, profile),
    path(URL.People.PROFILEEDIT, editProfile),
    path(URL.People.EXTENDEDBIOEDIT, editExtendedBio),
    path(URL.People.PROFILETAB, profileTab),
    path(URL.People.TIMELINE_CONTENT, timeline_content),
    path(URL.People.TOPICSEARCH, topicsSearch),
    path(URL.People.TOPICSUPDATE, topicsUpdate),
    path(URL.People.TAGSEARCH, tagsSearch),
    path(URL.People.TAGSUPDATE, tagsUpdate),
    path(URL.People.ZOMBIE, zombieProfile),
    # settings
    path(URL.People.SETTINGTAB, settingTab),
    path(URL.People.ACCOUNTPREFERENCES, accountprefs),
    # community
    path(URL.People.REPORT_CATEGORIES, reportCategories),
    path(URL.People.REPORT_USER, reportUser),
    path(URL.People.BLOCK_USER, blockUser),
    path(URL.People.UNBLOCK_USER, unblockUser),
    # webhook
    path(URL.People.GITHUB_EVENTS, githubEventsListener),
    # browse
    path(URL.People.BROWSE_SEARCH, browseSearch),
    path(URL.People.TOGGLE_ADMIRATION, toggleAdmiration),
    path(URL.People.ADMIRATIONS, profileAdmirations),
    # frameshots TODO
    path(URL.People.CREATE_FRAME, create_framework),
    path(URL.People.PUBLISH_FRAME, publish_framework),
    path(URL.People.FRAMEWORK, view_framework),
]
