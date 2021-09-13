from django.shortcuts import redirect
from django.http.response import HttpResponseForbidden
from django.conf import settings
from .strings import message
from .methods import allowBypassDeactivated
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


class ProfileActivationMiddleware(object):
    """
    For profile activation view redirection, if profile is inactive.
    """

    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        print(request.get_full_path())
        print(allowBypassDeactivated(request.get_full_path()))
        if request.user.is_authenticated and not request.user.profile.is_active:
            if request.method == 'POST' or request.headers.get('X-KNOT-REQ-SCRIPT', False)=='true':
                if not allowBypassDeactivated(request.get_full_path()):
                    return HttpResponseForbidden()
            if request.method == 'GET':
                if not (request.get_full_path().startswith(request.user.profile.getLink()) or allowBypassDeactivated(request.get_full_path()) or request.get_full_path().startswith(settings.MEDIA_URL)):
                    return redirect(request.user.profile.getLink())
        return self.get_response(request)


class TwoFactorMiddleware(object):
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request: WSGIRequest):
        # request.user.profile.two_factor_auth
        # if request.user.is_authenticated and True and not request.user.two_factorized:
        #     return redirect(URL.AUTH+'two_factor/setup')
        return self.get_response(request)
