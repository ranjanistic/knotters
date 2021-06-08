from moderation.apps import APPNAME
from django.apps import AppConfig

APPNAME = 'project'

class ServiceConfig(AppConfig):
    name = APPNAME
