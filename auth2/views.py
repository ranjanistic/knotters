from django.core.handlers.wsgi import WSGIRequest
from django.views.decorators.http import require_GET
from django.http.response import Http404, HttpResponse
from main.strings import Template,Code
from main.decorators import normal_profile_required
from main.methods import errorLog, respondJson, user_device_notify
from .methods import get_auth_section_html, renderer

@normal_profile_required
def notification_enabled(request: WSGIRequest) -> HttpResponse:
    user_device_notify(request.user, body='You have successfully enabled notifications.', title='Notifications Enabled')
    return respondJson(Code.OK)

@normal_profile_required
@require_GET
def auth_index(request:WSGIRequest):
    return renderer(request, Template.Auth.INDEX)

@normal_profile_required
@require_GET
def auth_index_tab(request:WSGIRequest, section:str):
    try:
        data = get_auth_section_html(request, section)
        if data:
            return HttpResponse(data)
        else:
            raise Exception('No such section')
    except Exception as e:
        errorLog(e)
        raise Http404(e)
