from django import urls
from .views import *

path = urls.path

urlpatterns = [
    path('reject',disapprove),
    path('<str:division>/<str:id>', moderation)
]
