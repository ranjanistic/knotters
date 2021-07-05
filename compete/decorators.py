from functools import wraps
from django.http.response import HttpResponseForbidden
from .models import CompetitionJudge

def judge_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            count = CompetitionJudge.objects.filter(judge=request.user.profile).count()
            if count > 0:
                return function(request, *args, **kwargs)
            else: raise Exception()
        except:
            raise HttpResponseForbidden()
    return wrap