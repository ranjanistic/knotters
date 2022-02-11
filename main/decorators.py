from json.decoder import JSONDecodeError
import traceback
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render

from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

from urllib.parse import unquote
import hmac
from hashlib import sha256
from django.views.decorators.csrf import csrf_exempt
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError
from django.utils.encoding import force_bytes

from functools import wraps
from ipaddress import ip_address, ip_network
from .methods import addMethodToAsyncQueue, errorLog
from .strings import Code, Event, AUTH2
from auth2.mailers import send_account_verification_email
import json
import requests
from django.conf import settings
from django.views.decorators.http import require_POST

from .env import INTERNAL_SHARED_SECRET, ISPRODUCTION, ISTESTING


def decDec(inner_dec):
    """
    Second order decorator
    """
    def dDmain(outer_dec):
        def decWrapper(f):
            wrapped = inner_dec(outer_dec(f))

            def fWrapper(*args, **kwargs):
                return wrapped(*args, **kwargs)
            return fWrapper
        return decWrapper
    return dDmain


@decDec(require_POST)
def require_JSON_body(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            loadedbody = json.loads(request.body.decode(Code.UTF_8))
            request.POST = dict(**loadedbody,**request.POST,JSON_BODY=True)
            return function(request, *args, **kwargs)
        except JSONDecodeError:
            if request.method == Code.POST:
                return function(request, *args, **kwargs)
            return HttpResponseNotAllowed(permitted_methods=[Code.POST])
    return wrap


def require_JSON(function):
    return require_JSON_body(function)


def decode_JSON(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            loadedbody = json.loads(request.body.decode(Code.UTF_8))
            request.POST = dict(**loadedbody,**request.POST,JSON_BODY=True)
            return function(request, *args, **kwargs)
        except JSONDecodeError:
            pass
        return function(request, *args, **kwargs)
    return wrap


def dev_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not ISPRODUCTION:
            return function(request, *args, **kwargs)
        else:
            raise Http404()

    return wrap

def verified_email_required(
    function=None, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME
):
    def decorator(view_func):
        @login_required(redirect_field_name=redirect_field_name, login_url=login_url)
        def _wrapped_view(request:WSGIRequest, *args, **kwargs):
            if not EmailAddress.objects.filter(
                user=request.user, verified=True
            ).exists() and not ISTESTING:
                # addMethodToAsyncQueue(f"{AUTH2}.mailers.{send_account_verification_email}", request)
                send_account_verification_email(request)
                return render(request, "account/verified_email_required.html")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


@decDec(verified_email_required)
def normal_profile_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_normal:
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('abnormal user')
            return HttpResponseForbidden('Abnormal user access')
    return wrap


@decDec(normal_profile_required)
def moderator_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_moderator:
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('Unauthorized moderator access')
            return HttpResponseForbidden('Unauthorized moderator access')
    return wrap

@decDec(normal_profile_required)
def mentor_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_mentor:
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('Unauthorized mentor access')
            return HttpResponseForbidden('Unauthorized mentor access')
    return wrap

@decDec(normal_profile_required)
def manager_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_manager():
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('Unauthorized manager access')
            return HttpResponseForbidden('Unauthorized management access')
    return wrap


@decDec(csrf_exempt)
def github_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if ISPRODUCTION:
            whitelist = requests.get(
                f'{settings.GITHUB_API_URL}/meta').json()['hooks']
            real_ip = u'{}'.format(request.META.get('HTTP_X_REAL_IP'))
            if not real_ip or real_ip == 'None':
                return HttpResponseForbidden('Permission denied 0')
            client_ip_address = ip_address(real_ip)
            for valid_ip in whitelist:
                if client_ip_address in ip_network(valid_ip):
                    break
            else:
                return HttpResponseForbidden('Permission denied 1')

            header_signature = request.META.get('HTTP_X_HUB_SIGNATURE_256')
            if header_signature is None:
                return HttpResponseForbidden('Permission denied 2')

            sha_name, signature = header_signature.split('=')
            if sha_name != Code.SHA256:
                return HttpResponseForbidden('Permission denied 3')

            mac = hmac.new(force_bytes(settings.GH_HOOK_SECRET),
                           msg=force_bytes(request.body), digestmod=sha256)
            if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
                return HttpResponseForbidden('Permission denied 4')

            try:
                ghevent = request.META.get('HTTP_X_GITHUB_EVENT', Event.PING)
                if ghevent == Event.PING:
                    return HttpResponse(Code.PONG)
                hookID = request.META.get('HTTP_X_GITHUB_DELIVERY', None)
                request.POST = dict(**request.POST, ghevent=ghevent, hookID=hookID, **json.loads(
                    unquote(request.body.decode(Code.UTF_8)).split('payload=')[1]))
                return function(request, *args, **kwargs)
            except Exception as e:
                errorLog(e)
                return HttpResponseBadRequest('Couldn\'t load request body properly.')
        else:
            return function(request, *args, **kwargs)
    return wrap


@decDec(csrf_exempt)
def github_bot_only(function):
    """
    For Knotters github bot events
    """
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            if request.headers['Authorization'] != INTERNAL_SHARED_SECRET:
                return HttpResponseForbidden('Permission denied 0')
            request.POST = json.loads(request.body.decode(Code.UTF_8))
            return function(request, *args, **kwargs)
        except Exception as e:
            errorLog(e)
            return HttpResponseBadRequest('Couldn\'t load request body properly.')
    return wrap
