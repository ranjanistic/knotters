from functools import wraps
from main.decorators import decDec
from django.http.response import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

@decDec(login_required)
def moderator_only(function):
  @wraps(function)
  def wrap(request, *args, **kwargs):
        if request.user.profile.is_moderator:
            return function(request, *args, **kwargs)
        else:
            return HttpResponseForbidden()

  return wrap