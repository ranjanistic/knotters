import json
import requests
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET
from django.utils import timezone
from django.shortcuts import redirect
from allauth.account.models import EmailAddress
from people.models import User
from moderation.models import LocalStorage
from projects.models import Project
from compete.models import Competition
from .env import ADMINPATH, SITE
from .methods import renderData, renderView
from .decorators import dev_only
from .methods import renderView, getDeepFilePaths, errorLog
from .settings import STATIC_URL, MEDIA_URL
from .strings import Code, COMPETE, URL, setPathParams


@require_GET
def offline(request: WSGIRequest) -> HttpResponse:
    return renderView(request, 'offline')


@require_GET
@dev_only
def mailtemplate(request: WSGIRequest, template: str) -> HttpResponse:
    return renderView(request, f'account/email/{template}')


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    projects = Project.objects.filter(status=Code.APPROVED)[0:3]
    data = {
        "projects": projects
    }
    try:
        comp = Competition.objects.get(endAt__lt=timezone.now)
        data["alert"] = {
            "message": f"The '{comp.title}' competition is on!",
            "URL": f"/{COMPETE}/{comp.id}"
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


class Manifest(TemplateView):
    content_type = 'application/json'
    template_name = "manifest.json"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sizes = []

        def appendWhen(path: str):
            condition = path.endswith('icon-circle.png')
            if condition:
                parts = path.split('/')
                size = int(parts[len(parts)-2])
                if not sizes.__contains__(size):
                    sizes.append(size)
            return condition

        assets = getDeepFilePaths(
            'static/graphics/self', appendWhen=appendWhen)

        icons = []

        for i in range(len(assets)):
            icons.append({
                'src': assets[i],
                'size': f"{sizes[i]}x{sizes[i]}"
            })

        context['icons'] = icons
        return context


class ServiceWorker(TemplateView):
    content_type = 'application/javascript'
    template_name = "service-worker.js"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        assets = []

        def appendWhen(path: str):
            return path.endswith(('.js', '.json', '.css', '.map', '.jpg', '.woff2', '.svg', '.png', '.jpeg')) and not (path.__contains__('/email/') or path.__contains__('/admin/'))
        assets = getDeepFilePaths(STATIC_URL.strip('/'), appendWhen=appendWhen)

        assets.append(f"/{URL.OFFLINE}")

        try:
            swassets = LocalStorage.objects.get(key=Code.SWASSETS)
            oldassets = json.loads(swassets.value)
            different = False
            if len(oldassets) != len(assets):
                different = True
            else:
                for old in oldassets:
                    if not assets.__contains__(old):
                        different = True
                        break
                if not different:
                    for new in assets:
                        if not oldassets.__contains__(new):
                            different = True
                            break

            assets = assets if different else oldassets
            if different:
                swassets.value = json.dumps(assets)
                swassets.save()
        except:
            LocalStorage.objects.update_or_create(
                key=Code.SWASSETS, value=json.dumps(assets))

        context = dict(**context, **renderData(dict(
            OFFLINE=f"/{URL.OFFLINE}",
            assets=json.dumps(assets),
            noOfflineList=json.dumps([
                setPathParams(
                    f"/{URL.COMPETE}{URL.Compete.COMPETETABSECTION}"),
                setPathParams(
                    f"/{URL.COMPETE}{URL.Compete.INDEXTAB}"),
                setPathParams(
                    f"/{URL.PEOPLE}{URL.People.SETTINGTAB}"),
                setPathParams(
                    f"/{URL.PEOPLE}{URL.People.PROFILETAB}"),
            ]),
            ignorelist=json.dumps([
                f"/{ADMINPATH}*",
                f"/{ADMINPATH}",
                f"/{URL.ROBOTS_TXT}",
                f"{MEDIA_URL}*",
                f"/{URL.REDIRECTOR}*",
                f"/{URL.ACCOUNTS}*",
                f"/{URL.MODERATION}*",
                f"/{URL.COMPETE}*",
                f"/{URL.LANDING}",
                setPathParams(f"/{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.People.SUCCESSORINVITE}"),
                setPathParams(f"/{URL.APPLANDING}"),
                setPathParams(f"/{URL.DOCTYPE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.CREATE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.PROJECTINFO}"),
            ]),
            recacheList=json.dumps([
                f"/{URL.REDIRECTOR}*",
                f"/{URL.ACCOUNTS}*",
                setPathParams(
                    f"/{URL.COMPETE}{URL.Compete.INVITEACTION}"),
                setPathParams(
                    f"/{URL.PEOPLE}{URL.People.PROFILEEDIT}"),
                setPathParams(
                    f"/{URL.PEOPLE}{URL.People.ACCOUNTPREFERENCES}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.PROFILEEDIT}"),
            ]),
        )))
        return context
