from functools import wraps
from hashlib import sha256
from hmac import compare_digest as hmac_compare_digest
from hmac import new as hmac_new
from ipaddress import ip_address, ip_network
from json import loads as json_loads
from json.decoder import JSONDecodeError
from urllib.parse import unquote

from allauth.account.models import EmailAddress
from auth2.mailers import send_account_verification_email
from deprecated.classic import deprecated
from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import (Http404, HttpResponse,
                                  HttpResponseBadRequest,
                                  HttpResponseForbidden,
                                  HttpResponseNotAllowed)
from django.shortcuts import render
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from requests import get as getRequest

from .env import ISTESTING
from .methods import errorLog
from .strings import Code, Event


def decDec(inner_dec: callable) -> callable:
    """To be used as a decorator to decorate a decorator.

    Args:
        inner_dec (callable): The inner decorator to be decorated.

    Returns:
        callable: The decorated decorator.
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
def require_JSON(function: callable) -> callable:
    """To make sure that the request method is POST and that the request body is a JSON object.
    If body is not a JSON object, then allows the request to continue if method is POST.

    Args:
        function (callable): The function to be decorated.

    Returns:
        HttpResponseNotAllowed: If the request is not a POST request and JSONDecodeError is raised.
        HttpResponseBadRequest: If any exception occurs while decoding the JSON object.
        callable: The decorated function.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        try:
            loadedbody = json_loads(request.body.decode(Code.UTF_8))
            request.POST = dict(**loadedbody, **request.POST, JSON_BODY=True)
            return function(request, *args, **kwargs)
        except Exception:
            if request.method == Code.POST:
                return function(request, *args, **kwargs)
            return HttpResponseNotAllowed(permitted_methods=[Code.POST])
    return wrap


@deprecated("Use @require_JSON instead")
def require_JSON_body(function):
    """Deprecated. Use @require_JSON instead."""
    return require_JSON(function)


def decode_JSON(function: callable) -> callable:
    """To decode the JSON object in the request body, if request is POSt.
    Does not however enforces request method to be POST.

    Args:
        function (callable): The function to be decorated.

    Returns:
        callable: The decorated function.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        try:
            if request.method == Code.POST:
                loadedbody = json_loads(request.body.decode(Code.UTF_8))
                request.POST = dict(
                    **loadedbody, **request.POST, JSON_BODY=True)
            return function(request, *args, **kwargs)
        except Exception:
            pass
        return function(request, *args, **kwargs)
    return wrap


def dev_only(function: callable) -> callable:
    """To make sure that the request is received in DEV environment

    Args:
        function (callable): The function to be decorated.

    Raises:
        Http404: If the request is not received in DEV environment.

    Returns:
        callable: The decorated function.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        if settings.DEBUG:
            return function(request, *args, **kwargs)
        else:
            raise Http404("NOT DEV ENVIRONMENT")

    return wrap


def verified_email_required(
    function: callable = None, login_url: str = None, redirect_field_name: str = REDIRECT_FIELD_NAME
) -> callable:
    """To make sure that the user has verified their email address. If not, then sends the verification email and
    renders the verification page.

    Args:
        function (callable): The function to be decorated.
        login_url (str): The URL to redirect to if the user is not logged in.
        redirect_field_name (str): The name of the GET parameter to use for the redirect URL.

    Returns:
        callable: The decorated function.
    """
    def decorator(view_func):
        @login_required(redirect_field_name=redirect_field_name, login_url=login_url)
        def _wrapped_view(request: WSGIRequest, *args, **kwargs):
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
def normal_profile_required(function: callable) -> callable:
    """To make sure that the requesting user has a normal profile.

    Args:
        function (callable): The function to be decorated.

    Raises:
        Http404: If the requesting user does not have a normal profile, and request method is GET.

    Returns:
        HttpResponseForbidden: If the requesting user does not have a normal profile, and request method is not GET.
        callable: The decorated function, if the requesting user has a normal profile.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        if request.user.profile.is_normal:
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('abnormal user', request.user)
            return HttpResponseForbidden('Abnormal user access', request.user)
    return wrap


@decDec(normal_profile_required)
def moderator_only(function: callable) -> callable:
    """To make sure that the requesting user is a moderator with normal profile.

    Args:
        function (callable): The function to be decorated.

    Raises:
        Http404: If the requesting user is not a moderator, and request method is GET.

    Returns:
        HttpResponseForbidden: If the requesting user is not a moderator, and request method is not GET.
        callable: The decorated function, if the requesting user is a moderator.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        if request.user.profile.is_moderator and not request.user.profile.is_mod_paused:
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('Unauthorized moderator access', request.user)
            return HttpResponseForbidden('Unauthorized moderator access', request.user)
    return wrap


@decDec(normal_profile_required)
def mentor_only(function: callable) -> callable:
    """To make sure that the requesting user is a mentor with normal profile.

    Args:
        function (callable): The function to be decorated.

    Raises:
        Http404: If the requesting user is not a mentor, and request method is GET.

    Returns:
        HttpResponseForbidden: If the requesting user is not a mentor, and request method is not GET.
        callable: The decorated function, if the requesting user is a mentor.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        if request.user.profile.is_mentor:
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('Unauthorized mentor access', request.user)
            return HttpResponseForbidden('Unauthorized mentor access', request.user)
    return wrap


@decDec(normal_profile_required)
def manager_only(function: callable) -> callable:
    """To make sure that the requesting user is a manager with normal profile.

    Args:
        function (callable): The function to be decorated.

    Raises:
        Http404: If the requesting user is not a manager, and request method is GET.

    Returns:
        HttpResponseForbidden: If the requesting user is not a manager, and request method is not GET.
        callable: The decorated function, if the requesting user is a manager.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        if request.user.profile.is_manager():
            return function(request, *args, **kwargs)
        else:
            if request.method == Code.GET:
                raise Http404('Unauthorized manager access', request.user)
            return HttpResponseForbidden('Unauthorized management access', request.user)
    return wrap


@decDec(csrf_exempt)
def github_only(function: callable) -> callable:
    """To make sure that the request is received from GitHub, by checking the following:
        1. The request IP is in the list of GitHub provided IPs.
        2. The request header contains the X-Hub-Signature-256 header,
            which is the HMAC-SHA-256 of the GitHub webhook payload.
        3. The request header contains the X-GitHub-Event header
        4. The request body is a valid JSON payload.


    Args:
        function (callable): The function to be decorated.

    Returns:
        HttpResponseForbidden: If the request is not received from GitHub.
        HttpResponseBadRequest: If the request is received from GitHub, but the request headers or body are invalid.
        callable: The decorated function, if the request is properly received from GitHub.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        if not settings.DEBUG:
            whitelist = getRequest(
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

            mac = hmac_new(force_bytes(settings.GH_HOOK_SECRET),
                           msg=force_bytes(request.body), digestmod=sha256)
            if not hmac_compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
                return HttpResponseForbidden('Permission denied 4')

            try:
                ghevent = request.META['HTTP_X_GITHUB_EVENT']
                if ghevent == Event.PING:
                    return HttpResponse(Code.PONG)
                hookID = request.META['HTTP_X_GITHUB_DELIVERY']
                request.POST = dict(**request.POST, ghevent=ghevent, hookID=hookID, **json_loads(
                    unquote(request.body.decode(Code.UTF_8)).split('payload=')[1]))
                return function(request, *args, **kwargs)
            except (JSONDecodeError, KeyError):
                return HttpResponseBadRequest('Couldn\'t load request properly.')
            except Exception as e:
                errorLog(e)
                return HttpResponseBadRequest('Error occurred.')
        else:
            return function(request, *args, **kwargs)
    return wrap


@decDec(csrf_exempt)
def github_bot_only(function: callable) -> callable:
    """To make sure that the request is received from a GitHub Bot, by checking the following:
        1. The request Authorization header contains the valid INTERNAL_SHARED_SECRET.
        2. The request body is a valid JSON payload.

    Args:
        function (callable): The function to be decorated.

    Returns:
        HttpResponseForbidden: If the request is not received from a GitHub Bot.
        HttpResponseBadRequest: If the request is received from a GitHub Bot, but the request headers or body are invalid.
        callable: The decorated function, if the request is properly received from a GitHub Bot.
    """
    @wraps(function)
    def wrap(request: WSGIRequest, *args, **kwargs):
        try:
            if request.headers['Authorization'] != settings.INTERNAL_SHARED_SECRET:
                return HttpResponseForbidden('Permission denied 0')
            request.POST = json_loads(request.body.decode(Code.UTF_8))
            return function(request, *args, **kwargs)
        except (JSONDecodeError, KeyError):
            return HttpResponseBadRequest('Couldn\'t load request properly.')
        except Exception as e:
            errorLog(e)
            return HttpResponseBadRequest('Error occurred.')
    return wrap
