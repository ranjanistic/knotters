import os
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.shortcuts import redirect
from allauth.account.models import EmailAddress
from people.models import User
import json
import requests
from projects.models import Project
from compete.models import Competition
from .env import ADMINPATH, SITE
from .methods import renderData, renderView, replaceUrlParamsWithStr
from .decorators import dev_only
from .methods import renderView, mapFilePaths
from .settings import BASE_DIR, STATIC_URL, MEDIA_URL
from .strings import code, COMPETE, url


@require_GET
def offline(request: WSGIRequest) -> HttpResponse:
    return renderView(request, 'offline')


@require_GET
@dev_only
def mailtemplate(request: WSGIRequest, template: str) -> HttpResponse:
    return renderView(request, f'account/email/{template}')


@require_GET
@dev_only
def createMockUsers(request: WSGIRequest, total: int) -> HttpResponse:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        for i in range(int(total)):
            r = requests.post(f'{SITE}/auth/signup/', headers=headers, data={
                              'email': f"testing{i}@knotters.org", "first_name": f"Testing{i}", 'password1': 'ABCD@12345678'})
            if r.status_code != 200:
                break
        EmailAddress.objects.filter(
            email__startswith=f"testing", email__endswith="@knotters.org").update(verified=True)
        return HttpResponse('ok')
    except Exception as e:
        return HttpResponse(str(e))


@require_GET
@dev_only
def clearMockUsers(request: WSGIRequest) -> HttpResponse:
    User.objects.filter(email__startswith=f"testing",
                        email__endswith="@knotters.org").delete()
    return HttpResponse('ok')


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    projects = Project.objects.filter(status=code.LIVE)[0:3]
    data = {
        "projects": projects
    }
    try:
        comp = Competition.objects.get(endAt__lt=timezone.now)
        data["alert"] = {
            "message": f"The '{comp.title}' competition is on!",
            "url": f"/{COMPETE}/{comp.id}"
        }
    except:
        pass
    return renderView(request, 'index', data)


@require_GET
def redirector(request: WSGIRequest) -> HttpResponse:
    next = request.GET.get('n', '/')
    next = '/' if str(next).strip() == '' or not next or next == 'None' else next
    if next.startswith("/"):
        return redirect(next)
    else:
        return renderView(request, 'forward', {'next': next})


@require_GET
def docIndex(request: WSGIRequest) -> HttpResponse:
    return renderView(request, "index", fromApp='docs')


@require_GET
def docs(request: WSGIRequest, type: str) -> HttpResponse:
    try:
        return renderView(request, type, fromApp='docs')
    except:
        raise Http404()


@require_GET
def landing(request: WSGIRequest) -> HttpResponse:
    return renderView(request, "landing")


@require_GET
def applanding(request: WSGIRequest, subapp: str) -> HttpResponse:
    return renderView(request, "landing", fromApp=subapp)


class Robots(TemplateView):
    content_type = 'text/plain'
    template_name = "robots.txt"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {
            'admin': ADMINPATH,
            'static': STATIC_URL,
            'media': MEDIA_URL
        }
        return context


class ServiceWorker(TemplateView):
    content_type = 'application/javascript'
    template_name = "service-worker.js"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        staticAssets = mapFilePaths(os.path.join(BASE_DIR, 'static/'))
        assets = []
        rep = str(os.getcwd()+"\\")
        for stat in staticAssets:
            path = str(stat).replace(rep, '/')
            if path.endswith(('.js', '.json', '.css', '.map', '.jpg', '.svg', '.png', '.woff2', '.jpeg')) and not assets.__contains__(path):
                assets.append(path)

        assets.append(f"/{url.OFFLINE}")
        context = renderData({
            'OFFLINE': f"/{url.OFFLINE}",
            'assets': json.dumps(assets),
            'noOfflineList': json.dumps([
                replaceUrlParamsWithStr(
                    f"/{url.COMPETE}{url.Compete.COMPETETABSECTION}"),
                replaceUrlParamsWithStr(
                    f"/{url.COMPETE}{url.Compete.INDEXTAB}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.SETTINGTAB}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.PROFILETAB}"),
            ]),
            'ignorelist': json.dumps([
                f"/{ADMINPATH}*",
                f"/{ADMINPATH}",
                f"/{url.ROBOTS_TXT}",
                f"{MEDIA_URL}*",
                f"/{url.REDIRECTOR}*",
                f"/{url.ACCOUNTS}*",
                f"/{url.MODERATION}*",
                f"/{url.COMPETE}*",
                f"/{url.LANDING}",
                replaceUrlParamsWithStr(f"/{url.APPLANDING}"),
                replaceUrlParamsWithStr(f"/{url.DOCTYPE}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.CREATE}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.PROJECTINFO}"),
            ]),
            'recacheList': json.dumps([
                f"/{url.REDIRECTOR}*",
                f"/{url.ACCOUNTS}*",
                replaceUrlParamsWithStr(
                    f"/{url.COMPETE}{url.Compete.INVITEACTION}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.PROFILEEDIT}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.ACCOUNTPREFERENCES}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.PROFILEEDIT}"),
            ]),
        })
        return context
