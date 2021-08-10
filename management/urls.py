from django.urls import path
from main.strings import URL
from .views import *


urlpatterns = [
    path(URL.INDEX, index),
    path(URL.Management.COMPETITIONS, competitions),
    path(URL.Management.CREATE_COMP, createCompete),
    path(URL.Management.COMPETITION, competition),
    path(URL.Management.SUBMIT_COMP, submitCompetition),

    path(URL.Management.REPORT_FEED, reportFeedbacks),
    path(URL.Management.REPORTS, reports),
    path(URL.Management.CREATE_REPORT, createReport),
    path(URL.Management.REPORT, report),
    path(URL.Management.FEEDBACKS, feedbacks),
    path(URL.Management.CREATE_FEED, createFeedback),
    path(URL.Management.FEEDBACK, feedback),
    path(URL.Management.COMMUNITY, community),
    path(URL.Management.MODERATORS, moderators),
    path(URL.Management.LABELS, labels),
    path(URL.Management.LABEL, label),
    path(URL.Management.LABEL_TOPICS, topics),
    path(URL.Management.LABEL_CATEGORYS, categories)
]