from django.core.handlers.wsgi import WSGIRequest
from django.core.exceptions import ObjectDoesNotExist
from main.methods import errorLog, respondJson
from main.strings import Code, Message
import jwt
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from main.decorators import knotters_only, require_POST, bearer_required, require_GET

@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def logintoken(request: WSGIRequest):
    if WSGIRequest.user.is_authenticated:
        try:
            token = jwt.encode(dict(id=request.user.profile.get_userid, exp=timezone.now()+timedelta(days=7)), settings.SECRET_KEY, algorithm="HS256")
            return respondJson(Code.OK, data=dict(token=token))
        except KeyError as k:
            print(k)
            return respondJson(Code.NO, error=Message.INVALID_REQUEST, status=400)
        except ObjectDoesNotExist:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST, status=404)
        except Exception as e:
            errorLog(e)
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)
    else:
        return respondJson(Code.NO, error=Message.USER_NOT_EXIST, status=404)
    
@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def mytoken(request: WSGIRequest):
    try:
        prof=request.user.profile()
        return respondJson(Code.OK, data=dict(user=dict(
                   id=prof.get_userid, name=prof.get_name, email=prof.get_email,is_moderator=prof.is_moderator, is_mentor=prof.is_mentor, is_verified=prof.is_verified, is_manager=prof.is_manager(), nickname=prof.nickname, picture=prof.get_abs_dp)))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)