from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from rjsmin import jsmin
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from django.http.response import Http404, HttpResponse
from people.models import User
from django.conf import settings
from main.strings import URL, Message, Template,Code
from main.decorators import manager_only, normal_profile_required, require_JSON
from main.methods import errorLog, respondJson, user_device_notify, renderData
from .methods import get_auth_section_html, renderer
from .apps import APPNAME


class NotifySW(TemplateView):
    content_type = Code.APPLICATION_JS
    template_name = Template.auth.notify_sw_js

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        stringrender = render_to_string(self.get_template_names(), request=self.request,context=context)
        try:
            if not settings.DEBUG:
                stringrender = jsmin(stringrender)
        except:
            pass
        return HttpResponse(stringrender, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = dict(**context, **renderData(dict(
            DEBUG=settings.DEBUG, OFFLINE=f"/{URL.OFFLINE}"), APPNAME))
        return context

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
            raise Exception('No section data')
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@normal_profile_required
@require_JSON
def verify_authorization(request:WSGIRequest):
    try:
        password = request.POST.get('password', None)
        verified = False
        if password:
            verified = request.user.check_password(request.user, request.POST.get('password'))
        if verified:
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)

@manager_only
@require_JSON
def change_ghorg(request:WSGIRequest):
    try:
        newghorgID = request.POST['newghorgID']
        if newghorgID == False:
            mgm = request.user.profile.update_management(githubOrgID=None)
        elif newghorgID not in map(lambda id: str(id), request.user.profile.get_ghOrgIDs()):
            raise ObjectDoesNotExist(newghorgID)
        else:
            mgm = request.user.profile.update_management(githubOrgID=str(newghorgID))
        if mgm:
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except (ObjectDoesNotExist, KeyError) as e:
        return respondJson(Code.NO,error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
