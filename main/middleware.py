from django.shortcuts import redirect
from .strings import URL, message
from .settings import MEDIA_URL
from django.core.handlers.wsgi import WSGIRequest

class MessageFilterMiddleware(object):
    """
    To filter alert/error messages provided via GET url queries, allowing only the messages derived from Message class of main.strings.

    This helps prevent malicious users from showing custom alerts via changing url alert query values.
    """
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request:WSGIRequest):
        if request.method == 'GET':
            request.GET._mutable = True
            alert = request.GET.get('a',None)
            error = request.GET.get('e',None)
            if not alert and not error:
                pass
            else:
                if error and not message.isValid(error):
                    request.GET['e'] = ''
                elif alert and not message.isValid(alert):
                    request.GET['a'] = ''
                else: pass
            request.GET._mutable = False
        return self.get_response(request)

class ProfileActivationMiddleware(object):
    """
    For profile activation view redirection, if profile is inactive and request method is GET.
    """
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request:WSGIRequest):
        if request.user.is_authenticated:
            if not request.user.profile.is_active:
                if request.method == 'GET' and not request.get_full_path().startswith(MEDIA_URL) and not request.get_full_path().__contains__(request.user.profile.getLink()) and not request.get_full_path().__contains__(URL.ACCOUNTS+'logout'):
                    return redirect(request.user.profile.getLink())
        return self.get_response(request)

class TwoFactorMiddleware(object):
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request:WSGIRequest):
        # request.user.profile.two_factor_auth
        # if request.user.is_authenticated and True and not request.user.two_factorized:
        #     return redirect(URL.ACCOUNTS+'two_factor/setup')
        return self.get_response(request)