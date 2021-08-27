from django.urls import path
from main.strings import URL
from .views import *


urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Management.COMPETITIONS, competitions),
    path(URL.Management.CREATE_COMP, createCompete),
    path(URL.Management.SUBMIT_COMP, submitCompetition),
    path(URL.Management.COMPETITION, competition),
    path(URL.Management.TOPICSEARCH, searchTopic),
    path(URL.Management.JUDGESEARCH, searchJudge),
    path(URL.Management.MODSEARCH, searchModerator),

    path(URL.Management.REPORT_FEED, reportFeedbacks),
    path(URL.Management.REPORTS, reports),
    path(URL.Management.CREATE_REPORT, createReport),
    path(URL.Management.REPORT, report),
    path(URL.Management.FEEDBACKS, feedbacks),
    path(URL.Management.CREATE_FEED, createFeedback),
    path(URL.Management.FEEDBACK, feedback),
    path(URL.Management.COMMUNITY, community),
    path(URL.Management.MODERATORS, moderators),
    path(URL.Management.ELGIBLE_MODSEARCH, searchEligibleModerator),
    path(URL.Management.ADD_MODERATOR, addModerator),
    path(URL.Management.REMOVE_MODERATOR, removeModerator),
    path(URL.Management.LABEL_CREATE, labelCreate),
    path(URL.Management.LABEL_UPDATE, labelUpdate),
    path(URL.Management.LABEL_DELETE, labelDelete),
    path(URL.Management.LABELS, labels),
    path(URL.Management.LABEL_TYPE, labelType),
    path(URL.Management.LABEL, label),
]