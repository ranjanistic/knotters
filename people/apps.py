from django.apps import AppConfig
from moderation.apps import APPNAME

APPNAME = 'people'


class PeopleConfig(AppConfig):
    name = APPNAME
