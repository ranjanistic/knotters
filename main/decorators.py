from urllib.parse import unquote
import hmac
from hashlib import sha256
from django.views.decorators.csrf import csrf_exempt
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError
from django.utils.encoding import force_bytes
from allauth.account.decorators import login_required
from functools import wraps
from ipaddress import ip_address, ip_network
from .methods import errorLog
from .strings import Code, Event
import json
import requests
from django.conf import settings
from django.views.decorators.http import require_POST

from .env import ISPRODUCTION


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
            request.POST = dict(**request.POST,**json.loads(request.body.decode(Code.UTF_8)),JSON_BODY=True)
            return function(request, *args, **kwargs)
        except Exception as e:
            if request.method == Code.POST:
                return function(request, *args, **kwargs)
            return HttpResponseNotAllowed(permitted_methods=[Code.POST])
    return wrap

def decode_JSON(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        try:
            request.POST = dict(**request.POST,**json.loads(request.body.decode(Code.UTF_8)),JSON_BODY=True)
            return function(request, *args, **kwargs)
        except Exception as e:
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


@decDec(login_required)
def normal_profile_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_normal:
            return function(request, *args, **kwargs)
        raise Http404()
    return wrap


@decDec(normal_profile_required)
def moderator_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_moderator:
            return function(request, *args, **kwargs)
        else:
            raise Http404()
    return wrap


@decDec(normal_profile_required)
def manager_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.profile.is_manager:
            return function(request, *args, **kwargs)
        else:
            if request.method == 'GET':
                raise Http404('Unauthorized manager access')
            return HttpResponseForbidden('Unauthorized access')
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
                request.POST = dict(**request.POST,ghevent=ghevent,hookID=hookID, **json.loads(
                    unquote(request.body.decode(Code.UTF_8)).split('payload=')[1]))
                return function(request, *args, **kwargs)
            except Exception as e:
                errorLog(e)
                return HttpResponseBadRequest('Couldn\'t load request body properly.')
        else:
            return function(request, *args, **kwargs)
    return wrap

@decDec(csrf_exempt)
def github_remote_only(function):
    """
    For not-owned by Knotters repositories
    """
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

            try:
                request.POST = dict(**request.POST, **json.loads(
                    unquote(request.body.decode(Code.UTF_8)).split('payload=')[1]))
                ghevent = request.META.get('HTTP_X_GITHUB_EVENT', Event.PING)
                if ghevent == Event.PING:
                    return HttpResponse(Code.OK)
                hookID = request.META.get('HTTP_X_GITHUB_DELIVERY', None)
                request.POST = dict(**request.POST,ghevent=ghevent,hookID=hookID)
                return function(request, *args, **kwargs)
            except Exception as e:
                errorLog(e)
                return HttpResponseBadRequest('Couldn\'t load request body properly.')
        else:
            return function(request, *args, **kwargs)
    return wrap
