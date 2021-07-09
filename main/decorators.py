
from django.http.response import HttpResponseForbidden, HttpResponseNotAllowed
from functools import wraps
import json

from .env import ISPRODUCTION
from django.views.decorators.http import require_POST

def decDec(inner_dec):
    """
    Second order decorator
    """
    def dDmain(outer_dec):
        def decWrapper(f):
            wrapped = inner_dec(outer_dec(f))
            def fWrapper(*args, **kwargs):
               return wrapped(*args, **kwargs)
            return fWrapper
        return decWrapper
    return dDmain


@decDec(require_POST)
def require_JSON_body(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            request.POST = json.loads(request.body.decode("utf-8"))
            return function(request, *args, **kwargs)
        except:
            return HttpResponseNotAllowed(permitted_methods=['POST'])
    return wrap


def dev_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not ISPRODUCTION:
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

    return wrap