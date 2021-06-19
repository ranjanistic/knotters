from django.urls import path
from main.views import landing
from .views import *

urlpatterns = [
    path('', index),
    path('landing', landing),
    path('indexTab/<str:tab>', indexTab),
    path('competeTab/<str:compID>/<str:section>', competitionTab),
    path('<str:compID>', competition),
]
