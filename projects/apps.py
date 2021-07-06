from moderation.apps import APPNAME
from django.apps import AppConfig

APPNAME = 'projects'

class ServiceConfig(AppConfig):
    name = APPNAME
