from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from auth2.models import DeviceNotification, EmailNotification, Notification
from webpush.models import Group
from main.strings import Template, Auth2
from main.methods import renderString, renderView
from .apps import APPNAME
from .receivers import *

def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))

def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    return renderString(request, file, data, fromApp=APPNAME)

def get_auth_section_data(requestUser, section):
    data = dict()
    if section == Auth2.DEVICE:
        pass
    if section == Auth2.ACCOUNT:
        pass
    if section == Auth2.SECURITY:
        pass
    if section == Auth2.PREFERENCE:
        pass
    if section == Auth2.NOTIFICATION:
        data['notifications'] = Notification.objects.filter(disabled=False)
        data['email_notifs'] = EmailNotification.objects.filter(subscribers=requestUser)
        data['device_notifs'] = DeviceNotification.objects.filter(subscribers=requestUser)
        pass
    return data
    
def get_auth_section_html(request, section):
    if section not in Auth2().AUTH2_SECTIONS:
        return False
    data = dict()
    for sec in Auth2().AUTH2_SECTIONS:
        if sec == section:
            data = get_auth_section_data(request.user,sec)
            break
    return renderer_stronly(request, section, data)
