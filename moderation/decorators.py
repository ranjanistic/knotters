from functools import wraps
from django.http.response import HttpResponseNotAllowed

def moderator_only(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
        if request.user.is_moderator:
            return function(request, *args, **kwargs)
        else:
            return HttpResponseNotAllowed()

  return wrap