import hmac
from hashlib import sha256
from django.views.decorators.csrf import csrf_exempt
from django.http.response import Http404, HttpResponseForbidden, HttpResponseNotAllowed, HttpResponseServerError
from django.utils.encoding import force_bytes
from functools import wraps
from ipaddress import ip_address, ip_network
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
            request.POST = json.loads(request.body.decode("utf-8"))
            return function(request, *args, **kwargs)
        except:
            return HttpResponseNotAllowed(permitted_methods=['POST'])
    return wrap


def dev_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if not ISPRODUCTION:
            return function(request, *args, **kwargs)
        else:
            raise Http404()

    return wrap


@decDec(csrf_exempt)
def github_only(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        forwarded_for = u'{}'.format(request.META.get('HTTP_X_FORWARDED_FOR'))
        if not forwarded_for or forwarded_for == 'None':
            return HttpResponseForbidden('Permission denied')

        client_ip_address = ip_address(forwarded_for)
        whitelist = requests.get(f'{settings.GITHUB_API_URL}/meta').json()['hooks']

        for valid_ip in whitelist:
            if client_ip_address in ip_network(valid_ip):
                break
        else:
            return HttpResponseForbidden('Permission denied')

        header_signature = request.META.get('HTTP_X_HUB_SIGNATURE_256')
        if header_signature is None:
            return HttpResponseForbidden('Permission denied')

        sha_name, signature = header_signature.split('=')
        if sha_name != 'sha256':
            return HttpResponseServerError('Operation not supported', status=501)

        mac = hmac.new(force_bytes(settings.SECRET_KEY), msg=force_bytes(request.body), digestmod=sha256)
        if not hmac.compare_digest(force_bytes(mac.hexdigest()), force_bytes(signature)):
            return HttpResponseForbidden('Permission denied')

        return function(request, *args, **kwargs)
    return wrap
