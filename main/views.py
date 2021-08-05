import json
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.http.response import Http404, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import redirect
from moderation.models import LocalStorage
from projects.models import Project
from people.models import Profile, Report
from .env import ADMINPATH
from .methods import renderData, renderView, respondJson
from .decorators import dev_only, require_JSON_body
from .methods import renderView, getDeepFilePaths
from .settings import STATIC_URL, MEDIA_URL
from .strings import Code, Message, URL, setPathParams


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
    data = dict(projects=projects)
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

@require_JSON_body
def reportFeedback(request:WSGIRequest) -> JsonResponse:
    email = request.POST.get('email',None)
    anonymous = not (email and str(email).strip())
    email = str(email).strip()
    reporter = None
    if not anonymous:
        if email == request.user.email:
            reporter = request.user.profile
        else:
            reporter = Profile.objects.filter(user__email__iexact=email).first()
            if not reporter: anonymous = True
    isReport = request.POST.get('isReport',True)
    summary = request.POST.get('summary','')
    detail = request.POST.get('detail','')
    report = Report.objects.create(isReport=isReport,reporter=reporter,summary=summary,detail=detail,anonymous=anonymous)
    return respondJson(Code.OK if report else Code.NO, error=Message.ERROR_OCCURRED if not report else '')

class Robots(TemplateView):
    content_type = 'text/plain'
    template_name = "robots.txt"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = dict(**context, admin=ADMINPATH,
                       static=STATIC_URL, media=MEDIA_URL)
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
            icons.append(dict(
                src=assets[i],
                size=f"{sizes[i]}x{sizes[i]}"
            ))

        context = dict(**context, icons=icons)
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
                setPathParams(f"/{URL.COMPETE}{URL.Compete.INDEXTAB}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.SETTINGTAB}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILETAB}"),
            ]),
            ignorelist=json.dumps([
                f"/{ADMINPATH}*",
                f"/{ADMINPATH}",
                f"/{URL.ROBOTS_TXT}",
                f"/{URL.REDIRECTOR}*",
                f"/{URL.ACCOUNTS}*",
                f"/{URL.MODERATION}*",
                f"/{URL.COMPETE}*",
                f"/{URL.LANDING}",
                f"/{URL.PROJECTS}{URL.Projects.ALLLICENSES}",
                f"/email/*",
                setPathParams(f"/{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.People.SUCCESSORINVITE}"),
                setPathParams(f"/{URL.APPLANDING}"),
                setPathParams(f"/{URL.DOCTYPE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROJECTINFO}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSES}"),
            ]),
            recacheList=json.dumps([
                f"/{URL.REDIRECTOR}*",
                f"/{URL.ACCOUNTS}*",
                setPathParams(f"/{URL.COMPETE}{URL.Compete.INVITEACTION}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILEEDIT}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ACCOUNTPREFERENCES}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILEEDIT}"),
            ]),
        )))
        return context
