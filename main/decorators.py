
from django.http.response import Http404, HttpResponseNotAllowed
from functools import wraps
import json
from .env import ISPRODUCTION


def require_JSON_body(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            request.POST = json.loads(request.body.decode("utf-8"))
            return function(request, *args, **kwargs)
        except:
            raise HttpResponseNotAllowed()

    return wrap


def dev_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not ISPRODUCTION:
            return function(request, *args, **kwargs)
        else:
            raise Http404()

    return wrap