from functools import wraps
from django.shortcuts import redirect

def profile_active_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.profile.is_active:
            return function(request, *args, **kwargs)
        return redirect(request.user.profile.getLink(alert="Account deactivated"))
    return wrap
