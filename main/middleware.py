from django.shortcuts import redirect
from .strings import url
from django.core.handlers.wsgi import WSGIRequest

class ProfileActivationMiddleware(object):
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request:WSGIRequest):
        if request.user.is_authenticated:
            if not request.user.profile.is_active and request.method == 'GET':
                if not request.get_full_path().__contains__(request.user.profile.getLink()) and not request.get_full_path().__contains__(url.ACCOUNTS+'logout'):
                    return redirect(request.user.profile.getLink())
        return self.get_response(request)

class TwoFactorMiddleware(object):
    def __init__(self, get_response) -> None:
        self.get_response = get_response
        super().__init__()

    def __call__(self, request:WSGIRequest):
        # request.user.profile.two_factor_auth
        # if request.user.is_authenticated and True and not request.user.two_factorized:
        #     return redirect(url.ACCOUNTS+'two_factor/setup')
        return self.get_response(request)