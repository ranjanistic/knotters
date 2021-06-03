from django import urls
from .views import *

path = urls.path

urlpatterns = [
    path('<str:division>/<str:id>', moderation)
]
