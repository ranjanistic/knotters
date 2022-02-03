from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from auth2.models import DeviceNotification, EmailNotification
from django.views.decorators.http import require_GET
from django.http.response import Http404, HttpResponse
from django.conf import settings
from main.strings import Message, Template, Code
from main.decorators import manager_only, normal_profile_required, require_JSON
from main.methods import errorLog, respondJson, user_device_notify, renderData
from .methods import get_auth_section_html, renderer
from .apps import APPNAME


@normal_profile_required
def notification_enabled(request: WSGIRequest) -> HttpResponse:
    user_device_notify(
        request.user, body='You have successfully enabled notifications.', title='Notifications Enabled')
    return respondJson(Code.OK)


@normal_profile_required
@require_GET
def auth_index(request: WSGIRequest):
    return renderer(request, Template.Auth.INDEX)


@normal_profile_required
@require_GET
def auth_index_tab(request: WSGIRequest, section: str):
    try:
        data = get_auth_section_html(request, section)
        if data:
            return HttpResponse(data)
        else:
            raise Exception('No section data')
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def verify_authorization(request: WSGIRequest):
    try:
        password = request.POST.get('password', None)
        verified = False
        if password:
            verified = request.user.check_password(
                request.user, request.POST.get('password'))
        if verified:
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@manager_only
@require_JSON
def change_ghorg(request: WSGIRequest):
    try:
        newghorgID = request.POST['newghorgID']
        if newghorgID == False:
            mgm = request.user.profile.update_management(githubOrgID=None)
        elif newghorgID not in map(lambda id: str(id), request.user.profile.get_ghOrgIDs()):
            raise ObjectDoesNotExist(newghorgID)
        else:
            mgm = request.user.profile.update_management(
                githubOrgID=str(newghorgID))
        if mgm:
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except (ObjectDoesNotExist, KeyError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def email_notification_toggle(request: WSGIRequest, notifID: UUID):
    try:
        subscribe = request.POST['subscribe']
        denotif = EmailNotification.objects.get(notification__id=notifID)
        if not subscribe:
            denotif.subscribers.remove(request.user)
        else:
            denotif.subscribers.add(request.user)
        return respondJson(Code.OK)
    except (KeyError, ObjectDoesNotExist) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def device_notifcation_toggle(request: WSGIRequest, notifID: UUID):
    try:
        subscribe = request.POST['subscribe']
        denotif = DeviceNotification.objects.get(notification__id=notifID)
        if not subscribe:
            denotif.subscribers.remove(request.user)
        else:
            denotif.subscribers.add(request.user)
        return respondJson(Code.OK)
    except (KeyError, ObjectDoesNotExist) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
