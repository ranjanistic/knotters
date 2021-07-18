from functools import wraps
from main.strings import URL
from main.decorators import decDec
from allauth.account.decorators import login_required
from django.shortcuts import redirect

@decDec(login_required)
def profile_active_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_active:
            return function(request, *args, **kwargs)
        return redirect(request.user.profile.getLink(alert="Account deactivated"))
    return wrap
