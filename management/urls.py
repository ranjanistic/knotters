from django.urls import path
from main.strings import URL
from .views import *


urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Management.CONTACT_REQUEST_CATEGORIES, contact_categories),
    path(URL.Management.CONTACT_SUBM, contact_subm),
    path(URL.Management.COMPETITIONS, competitions),
    path(URL.Management.CREATE_COMP, createCompete),
    path(URL.Management.SUBMIT_COMP, submitCompetition),
    path(URL.Management.EDIT_COMP, editCompetition),
    path(URL.Management.DRAFT_DEL_COMP, draftDeleteCompete),
    path(URL.Management.COMPETITION, competition),
    path(URL.Management.TOPICSEARCH, searchTopic),
    path(URL.Management.MNTSEARCH, searchMentor),
    path(URL.Management.MODSEARCH, searchModerator),

    path(URL.Management.CREATE_REPORT, createReport),
    path(URL.Management.CREATE_FEED, createFeedback),
    path(URL.Management.REPORT_FEED, reportFeedbacks),
    path(URL.Management.REPORT_FEED_TYPE, reportfeedType),
    path(URL.Management.REPORT_FEED_TYPEID, reportfeedTypeID),

    path(URL.Management.COMMUNITY, community),

    path(URL.Management.MODERATORS, moderators),
    path(URL.Management.ELGIBLE_MODSEARCH, searchEligibleModerator),
    path(URL.Management.ADD_MODERATOR, addModerator),
    path(URL.Management.REMOVE_MODERATOR, removeModerator),

    path(URL.Management.MENTORS, mentors),
    path(URL.Management.ELGIBLE_MNTSEARCH, searchEligibleMentor),
    path(URL.Management.ADD_MENTOR, addMentor),
    path(URL.Management.REMOVE_MENTOR, removeMentor),

    path(URL.Management.LABEL_CREATE, labelCreate),
    path(URL.Management.LABEL_UPDATE, labelUpdate),
    path(URL.Management.LABEL_DELETE, labelDelete),
    path(URL.Management.LABELS, labels),
    path(URL.Management.LABEL_TYPE, labelType),
    path(URL.Management.LABEL, label),

    path(URL.Management.PEOPLE_MGM_SEND_INVITE, sendPeopleInvite),
    path(URL.Management.PEOPLE_MGM_INVITE, peopleMGMInvitation),
    path(URL.Management.PEOPLE_MGM_INVITE_ACT, peopleMGMInvitationAction),
    path(URL.Management.PEOPLE_MGM_REMOVE, peopleMGMRemove),

]