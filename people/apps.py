from moderation.apps import APPNAME
from django.apps import AppConfig

APPNAME = 'people'

class PeopleConfig(AppConfig):
    name = APPNAME
