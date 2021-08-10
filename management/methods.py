from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from main.methods import errorLog, renderView, renderString
from main.strings import URL
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)