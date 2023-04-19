from django.core.handlers.wsgi import WSGIRequest
from allauth.account.models import EmailAddress
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from auth2.models import APIKey

from main.decorators import knotters_only, require_POST, bearer_required, require_GET, normal_profile_required
from main.methods import errorLog, respondJson
from main.strings import COMPETE, URL, Action, Code, Message
import jwt
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from people.models import Profile

@csrf_exempt
def status(request):
    return respondJson(Code.OK)

@csrf_exempt
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
            if not emailAddr.user.check_password(password):
                return respondJson(Code.NO, error=Message.INVALID_CREDENTIALS, status=401)
        else:
            key = APIKey.objects.get(key=apiKey)
            profile = key.profile
        if not profile.isNormal():
            raise ObjectDoesNotExist("Abnormal profile")
        if tokenize:
            token = jwt.encode(dict(id=profile.get_userid, exp=timezone.now()+timedelta(days=7)), settings.SECRET_KEY, algorithm="HS256")
            return respondJson(Code.OK, data=dict(token=token))
        return respondJson(Code.OK, data=dict(user=dict(
                   id=profile.get_userid, name=profile.get_name, email=profile.get_email, is_moderator=profile.is_moderator, is_mentor=profile.is_mentor, is_verified=profile.is_verified,is_manager=profile.is_manager(), nickname=profile.nickname, picture=profile.get_abs_dp)))
    except KeyError:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST, status=400)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.USER_NOT_EXIST, status=404)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)


@csrf_exempt
@normal_profile_required
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
@normal_profile_required
@require_GET
def getSessionUser(request: WSGIRequest):
    try:
        profile:Profile = request.user.profile
        return respondJson(Code.OK, data=dict(user=dict(
                   id=profile.get_userid, name=profile.get_name, email=profile.get_email,is_moderator=profile.is_moderator, 
                   is_mentor=profile.is_mentor, is_verified=profile.is_verified, is_manager=profile.is_manager(), 
                   nickname=profile.nickname, picture=profile.get_abs_dp, profile=profile.get_abs_link
                )))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)

