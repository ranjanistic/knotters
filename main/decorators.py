
from functools import wraps
from django.http.response import HttpResponseNotAllowed
from django.views.decorators.http import require_POST
import json

def require_JSON_body(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
    try:
        request.POST = json.loads(request.body.decode("utf-8"))
        return function(request, *args, **kwargs)
    except:
        raise HttpResponseNotAllowed()

  return wrap