from django.core.handlers.wsgi import WSGIRequest
from main.decorators import manager_only
from .methods import renderer

@manager_only
def index(request:WSGIRequest):
    return renderer(request,'index')
