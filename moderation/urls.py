from django import urls
from .views import *

path = urls.path

urlpatterns = [
    path('reject',disapprove),
    path('approve',approve),
    path('<str:division>/<str:id>', moderation)
]
