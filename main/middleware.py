from django.shortcuts import redirect
from htmlmin.minify import html_minify
from django.http.response import HttpResponseForbidden
from django.urls import resolve
from ipaddress import ip_address
from django.utils.deprecation import MiddlewareMixin
import time
from allauth_2fa.middleware import AllauthTwoFactorMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.sessions.backends.base import UpdateError
from django.core.exceptions import SuspiciousOperation
from django.utils.cache import patch_vary_headers
from django.utils.http import http_date
from django.conf import settings
from .strings import message, URL, Code
from .env import ADMINPATH
from .methods import allowBypassDeactivated, activity
from django.core.handlers.wsgi import WSGIRequest


class MessageFilterMiddleware(object):
    """
    To filter alert/error messages provided via GET url queries, allowing only the messages derived from Message class of main.strings.

    This helps prevent malicious users from showing custom alerts via changing url alert query values.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        if request.method == 'GET':
            request.GET._mutable = True
            alert = request.GET.get('a', None)
            error = request.GET.get('e', None)
            success = request.GET.get('s', None)
            if not (alert or error or success):
                pass
            else:
                if error and not message.isValid(error):
                    request.GET['e'] = ''
                if alert and not message.isValid(alert):
                    request.GET['a'] = ''
                if success and not message.isValid(success):
                    request.GET['s'] = ''
            request.GET._mutable = False
        return self.get_response(request)


class MinifyMiddleware(object):

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        response = self.get_response(request)
        if not settings.DEBUG:
            if response.status_code == 200 and response['Content-Type'] == f'text/html; charset={Code.UTF_8}':
                minified = html_minify(response.content.decode(Code.UTF_8))
                response.content = minified.encode(Code.UTF_8)
        return response

class ActivityMiddleware(object):

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        real_ip = u'{}'.format(request.META.get('HTTP_X_REAL_IP'))
        if real_ip and real_ip != 'None':
            client_ip_address = ip_address(real_ip)
            # print(client_ip_address)

        def addslash(path):
            return f"/{path}" if not path.startswith('/') else path
        if not (request.path.startswith(f"/{ADMINPATH}") or list(map(addslash, [URL.SERVICE_WORKER])).__contains__(request.path)):
            activity(request, self.get_response(request))
        return self.get_response(request)


class AuthAccessMiddleware(object):

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        real_ip = u'{}'.format(request.META.get('HTTP_X_REAL_IP'))
        if real_ip and real_ip != 'None':
            client_ip_address = ip_address(real_ip)
            if request.user.is_authenticated:
                request.session['ip_address'] = client_ip_address
                # print(client_ip_address)

        return self.get_response(request)


class ProfileActivationMiddleware(object):
    """
    For profile activation view redirection, if profile is inactive.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        if request.user.is_authenticated and not request.user.profile.is_active:
            if request.method == 'POST' or request.headers.get('X-KNOT-REQ-SCRIPT', False) == 'true':
                if not allowBypassDeactivated(request.get_full_path()):
                    return HttpResponseForbidden()
            if request.method == 'GET':
                if not (request.get_full_path().startswith(request.user.profile.getLink()) or allowBypassDeactivated(request.get_full_path())):
                    return redirect(request.user.profile.getLink())
        return self.get_response(request)


class TwoFactorMiddleware(AllauthTwoFactorMiddleware):
    """
    For two factor session key management.
    """

    def process_request(self, request):
        match = resolve(request.path)
        except_list = getattr(settings, 'BYPASS_2FA_PATHS', ())
        except_list += ('/auth/two-factor-authenticate',)
        if (request.path.strip('/') not in except_list) and (not match.url_name or not match.url_name.startswith(except_list)):
            dele = True
            for p in except_list:
                if request.path == p:
                    dele = False
                    break
                elif request.path.startswith(p):
                    dele = False
                    break
                elif request.path.strip('/').startswith(p):
                    dele = False
                    break
                elif request.path.strip('/').startswith(p.strip('/')):
                    dele = False
                    break
            try:
                if dele:
                    del request.session['allauth_2fa_user_id']
            except KeyError:
                pass


class ExtendedSessionMiddleware(SessionMiddleware):
    """
    To extended session expiry date on every request.
    """

    def process_response(self, request: WSGIRequest, response):
        """
        If request.session was modified, or if the configuration is to save the
        session every time, save the changes and set a session cookie or delete
        the session cookie if the session has been emptied.
        """
        try:
            accessed = request.session.accessed
            modified = request.session.modified
            empty = request.session.is_empty()
        except AttributeError:
            return response

        if settings.SESSION_COOKIE_NAME in request.COOKIES and empty:
            response.delete_cookie(
                settings.SESSION_COOKIE_NAME,
                path=settings.SESSION_COOKIE_PATH,
                domain=settings.SESSION_COOKIE_DOMAIN,
            )
            patch_vary_headers(response, ('Cookie',))
        else:
            if accessed:
                patch_vary_headers(response, ('Cookie',))
            if not empty:

                max_age = request.session.get_expiry_age()
                expires_time = time.time() + max_age
                expires = http_date(expires_time)

                if response.status_code != 500:
                    try:
                        request.session.save()
                    except UpdateError:
                        return response

                    response.set_cookie(
                        settings.SESSION_COOKIE_NAME,
                        request.session.session_key, max_age=max_age,
                        expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=settings.SESSION_COOKIE_SECURE or None,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                    )
        return response


class XForwardedForMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if "HTTP_X_FORWARDED_FOR" in request.META:
            request.META["HTTP_X_PROXY_REMOTE_ADDR"] = request.META["REMOTE_ADDR"]
            parts = request.META["HTTP_X_FORWARDED_FOR"].split(",", 1)
            request.META["REMOTE_ADDR"] = parts[0]
