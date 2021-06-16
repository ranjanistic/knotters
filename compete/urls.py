from django.urls import path
from .views import *

urlpatterns = [
    path('', index),
    path('competeTab/<str:compID>/<str:section>', competitionTab),
    path('<str:compID>', competition),
]
