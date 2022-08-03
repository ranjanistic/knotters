from django.urls import path
from main.strings import URL

from .views import *

urlpatterns = [
    path(URL.INDEX, index),
    # Licenses
    path(URL.Projects.ALLLICENSES, allLicences),
    path(URL.Projects.LICENSE, licence),
    path(URL.Projects.ADDLICENSE, addLicense),
    path(URL.Projects.PUB_LICENSES, public_licenses),
    path(URL.Projects.LICENSE_SEARCH, licenseSearch),
    path(URL.Projects.LICENSES, licences),
    # Projects creation/deletion
    path(URL.Projects.CREATEVALIDATEFIELD, validateField),
    path(URL.Projects.CREATE, create),
    path(URL.Projects.CREATE_FREE, createFree),
    path(URL.Projects.CREATE_MOD, createMod),
    path(URL.Projects.CREATE_CORE, createCore),
    path(URL.Projects.SUBMIT_FREE, submitFreeProject),
    path(URL.Projects.SUBMIT_MOD, submitProject),
    path(URL.Projects.SUBMIT_CORE, submitCoreProject),
    path(URL.Projects.ACCEPT_TERMS, acceptTerms),
    path(URL.Projects.TRASH, trashProject),
    # Projects profile
    path(URL.Projects.AT_NICKANAME, at_nickname),
    path(URL.Projects.PROFILE_BASE, profileBase),
    path(URL.Projects.PROFILE_MOD, profileMod),
    path(URL.Projects.PROFILE_FREE, profileFree),
    path(URL.Projects.PROFILE_CORE, profileCore),
    path(URL.Projects.PROFILEEDIT, editProfile),
    # Projects assets
    path(URL.Projects.MANAGE_ASSETS, manageAssets),
    # Projects topics/tags
    path(URL.Projects.TOPICSEARCH, topicsSearch),
    path(URL.Projects.TOPICSUPDATE, topicsUpdate),
    path(URL.Projects.TAGSEARCH, tagsSearch),
    path(URL.Projects.TAGSUPDATE, tagsUpdate),
    # Projects repository
    path(URL.Projects.USER_GH_REPOS, userGithubRepos),
    path(URL.Projects.LINK_FREE_REPO, linkFreeGithubRepo),
    path(URL.Projects.UNLINK_FREE_REPO, unlinkFreeGithubRepo),

    path(URL.Projects.LIVEDATA, liveData),
    # Projects github
    path(URL.Projects.GITHUB_EVENTS, githubEventsListener),
    path(URL.Projects.GITHUB_BOT_EVENTS, githubBotEvents),
    # Projects reporting
    path(URL.Projects.REPORT_CATEGORIES, reportCategories),
    path(URL.Projects.REPORT_PROJECT, reportProject),
    path(URL.Projects.REPORT_SNAPSHOT, reportSnapshot),

    path(URL.Projects.BROWSE_SEARCH, browseSearch),
    # Projects snapshots
    path(URL.Projects.SNAPSHOTS, snapshots),
    path(URL.Projects.SNAPSHOT, snapshot),
    # Admirations
    path(URL.Projects.TOGGLE_ADMIRATION, toggleAdmiration),
    path(URL.Projects.ADMIRATIONS, projectAdmirations),
    path(URL.Projects.TOGGLE_SNAP_ADMIRATION, toggleSnapAdmiration),
    path(URL.Projects.SNAP_ADMIRATIONS, snapAdmirations),
    # Projects ownership
    path(URL.Projects.INVITE_PROJECT_OWNER, handleOwnerInvitation),
    path(URL.Projects.PROJECT_TRANS_INVITE, projectTransferInvite),
    path(URL.Projects.PROJECT_TRANS_INVITE_ACT, projectTransferInviteAction),
    # Verfiied Projects moderatorship
    path(URL.Projects.INVITE_VERPROJECT_MOD, handleVerModInvitation),
    path(URL.Projects.VER_MOD_TRANS_INVITE, projectModTransferInvite),
    path(URL.Projects.VER_MOD_TRANS_INVITE_ACT, projectModTransferInviteAction),
    # Core Projects moderatorship
    path(URL.Projects.INVITE_COREPROJECT_MOD, handleCoreModInvitation),
    path(URL.Projects.CORE_MOD_TRANS_INVITE, coreProjectModTransferInvite),
    path(URL.Projects.CORE_MOD_TRANS_INVITE_ACT,
         coreProjectModTransferInviteAction),
    # Projects deletion
    path(URL.Projects.VER_DEL_REQUEST, verProjectDeleteRequest),
    path(URL.Projects.VER_DEL_REQUEST_ACT, verProjectDeleteRequestAction),
    path(URL.Projects.CORE_DEL_REQUEST, coreProjectDeleteRequest),
    path(URL.Projects.CORE_DEL_REQUEST_ACT, coreProjectDeleteRequestAction),
    # Quick(Free)/Core Projects verification
    path(URL.Projects.FREE_VERIFICATION_REQUEST, freeVerificationRequest),
    path(URL.Projects.CORE_VERIFICATION_REQUEST, coreVerificationRequest),
    # Projects cocreators
    path(URL.Projects.INVITE_PROJECT_COCREATOR, handleCocreatorInvitation),
    path(URL.Projects.VIEW_COCREATOR_INVITE, projectCocreatorInvite),
    path(URL.Projects.COCREATOR_INVITE_ACT, projectCocreatorInviteAction),
    path(URL.Projects.MANAGE_PROJECT_COCREATOR, projectCocreatorManage),
    # Project Raters
    path(URL.Projects.PROJECT_RATING_SUBMIT, submitProjectRating)
]
