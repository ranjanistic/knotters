from django.apps import AppConfig
from moderation.apps import APPNAME

APPNAME = 'projects'


class ServiceConfig(AppConfig):
    name = APPNAME
