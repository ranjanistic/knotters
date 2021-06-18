from django.urls import path
from main.views import landing
from .views import *

urlpatterns = [
    path('', index),
    path('landing', landing),
    path('competeTab/<str:compID>/<str:section>', competitionTab),
    path('<str:compID>', competition),
]
