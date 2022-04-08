from django.urls import path
from main.strings import URL

from .views import *

urlpatterns = [
    path(URL.Moderation.MODID, moderation),
    path(URL.Moderation.MESSAGE, message),
    path(URL.Moderation.ACTION, action),
    path(URL.Moderation.REAPPLY, reapply),
    path(URL.Moderation.APPROVECOMPETE, approveCompetition),

    path(URL.Moderation.REPORT_CATEGORIES, reportCategories),
    path(URL.Moderation.REPORT_MODERATION, reportModeration),
]
