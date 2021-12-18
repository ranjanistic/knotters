from functools import wraps
from deprecated import deprecated
from django.http.response import HttpResponseForbidden
from .models import CompetitionJudge
from main.decorators import decDec
from django.contrib.auth.decorators import login_required

@deprecated(reason='Use the new mentor_only decorator')
@decDec(login_required)
def judge_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            if CompetitionJudge.objects.filter(judge=request.user.profile).exists():
                return function(request, *args, **kwargs)
            else: raise Exception()
        except:
            return HttpResponseForbidden()
    return wrap

@decDec(login_required)
def mentor_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            if request.user.profile.is_mentor:
                return function(request, *args, **kwargs)
            else: raise Exception()
        except:
            return HttpResponseForbidden()
    return wrap