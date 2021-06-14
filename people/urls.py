from django.urls import path

from .views import *

urlpatterns = [
    path('', index),
    path('profile/<str:userID>', profile),
    path('profile/edit/<str:section>', editProfile),
    path('profiletab/<str:userID>/<str:section>', profileTab),
    path('settingtab/<str:section>', settingTab)
]
