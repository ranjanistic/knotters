from django.core.handlers.wsgi import WSGIRequest
from allauth.account.models import EmailAddress
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from management.models import APIKey

from main.decorators import knotters_only, require_JSON, decode_JSON,require_POST, bearer_required, require_GET
from main.methods import (base64ToImageFile, errorLog, respondJson,
                          respondRedirect)
from main.strings import COMPETE, URL, Action, Code, Message, Template
import jwt
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

@csrf_exempt
@knotters_only
@require_POST
def verifyCredentials(request: WSGIRequest):
    try:
        apiKey = request.POST.get("apiKey", None)
        tokenize = request.POST.get("tokenize", False)
        profile = None
        if not apiKey:
            email = request.POST["email"][:80]
            password = request.POST["password"][:100]
            emailAddr = EmailAddress.objects.get(email=email, verified=True)
            profile = emailAddr.user.profile
        else:
            key = APIKey.objects.get(key=apiKey)
            profile = key.profile
        if not profile.isNormal():
            raise ObjectDoesNotExist("Abnormal profile")
        if tokenize:
            token = jwt.encode(dict(id=profile.get_userid, exp=timezone.now()+timedelta(days=7)), settings.SECRET_KEY, algorithm="HS256")
            return respondJson(Code.OK, data=dict(token=token))
        return respondJson(Code.OK, data=dict(user=dict(
                   id=profile.get_userid, name=profile.get_name, is_moderator=profile.is_moderator, is_mentor=profile.is_mentor, is_verified=profile.is_verified, nickname=profile.nickname)))
    except KeyError:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST, status=400)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.USER_NOT_EXIST, status=404)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)


@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def refreshToken(request: WSGIRequest):
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



@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def tokenUser(request: WSGIRequest):
    try:
        profile = request.user.profile
        return respondJson(Code.OK, data=dict(user=dict(
                   id=profile.get_userid, name=profile.get_name, is_moderator=profile.is_moderator, is_mentor=profile.is_mentor, is_verified=profile.is_verified, nickname=profile.nickname)))
        print(request.user)
        token = jwt.encode(dict(id=request.user.profile.get_userid, exp=timezone.now()+timedelta(minutes=5)), settings.SECRET_KEY, algorithm="HS256")
        return respondJson(Code.OK, data=dict(token=token))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)

