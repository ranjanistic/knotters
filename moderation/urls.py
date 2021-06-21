from django.urls import path
from main.strings import url
from .views import *

urlpatterns = [
    path('reject',disapprove),
    path('approve',approve),
    path('<str:division>/<str:id>', moderation),
    # path(url.Moderation.REJECT, disapprove),
    # path(url.Moderation.APPROVE, approve),
    # path(url.Moderation.DIVISIONID, moderation)
]
