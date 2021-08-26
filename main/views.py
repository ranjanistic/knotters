import json
from django.utils import timezone
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from django.conf import settings
from django.shortcuts import redirect
from moderation.models import LocalStorage
from projects.models import LegalDoc, Project
from compete.models import Competition
from people.models import Profile
from people.methods import rendererstr as peopleRendererstr
from projects.methods import rendererstr as projectsRendererstr
from .env import ADMINPATH
from .methods import errorLog, renderData, renderView
from .decorators import dev_only
from .methods import renderView, getDeepFilePaths
from .strings import Code, URL, setPathParams, Template, DOCS, COMPETE, PEOPLE, PROJECTS

@require_GET
def offline(request: WSGIRequest) -> HttpResponse:
    return renderView(request, Template.OFFLINE)


@require_GET
@dev_only
def mailtemplate(request: WSGIRequest, template: str) -> HttpResponse:
    return renderView(request, f'account/email/{template}')

@require_GET
@dev_only
def template(request: WSGIRequest, template: str) -> HttpResponse:
    return renderView(request, template)


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    comp = Competition.objects.filter(startAt__lt=timezone.now(),endAt__gte=timezone.now()).first()
    data = dict()
    if comp:
        data = dict(
            alert=dict(
                message=f"'{comp.title}' competition is happening!",
                url=comp.getLink(),
            )
        )
    return renderView(request, Template.INDEX,data)


@require_GET
def redirector(request: WSGIRequest) -> HttpResponse:
    next = request.GET.get('n', '/')
    next = '/' if str(next).strip() == '' or not next or next == 'None' else next
    if next.startswith("/"):
        return redirect(next)
    else:
        return renderView(request, Template.FORWARD, dict(next=next))


@require_GET
def docIndex(request: WSGIRequest) -> HttpResponse:
    docs = LegalDoc.objects.all()
    return renderView(request, Template.Docs.INDEX, fromApp=DOCS, data=dict(docs=docs))


@require_GET
def docs(request: WSGIRequest, type: str) -> HttpResponse:
    try:
        doc = LegalDoc.objects.get(pseudonym=type)
        return renderView(request, Template.Docs.DOC, fromApp=DOCS, data=dict(doc=doc))
    except Exception as e:
        errorLog(e)
        try:
            return renderView(request, type, fromApp=DOCS)
        except Exception as e:
            errorLog(e)
            raise Http404()


@require_GET
def landing(request: WSGIRequest) -> HttpResponse:
    return renderView(request, Template.LANDING)


@require_GET
def applanding(request: WSGIRequest, subapp: str) -> HttpResponse:
    if subapp == COMPETE:
        template = Template.Compete.LANDING
    elif subapp == PEOPLE:
        template = Template.People.LANDING
    elif subapp == PROJECTS:
        template = Template.Projects.LANDING
    else:
        raise Http404()
    return renderView(request, template, fromApp=subapp)


class Robots(TemplateView):
    content_type = Code.TEXT_PLAIN
    template_name = Template.ROBOTS_TXT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context = dict(**context,static=settings.STATIC_URL, media=settings.MEDIA_URL)
        return context


class Manifest(TemplateView):
    content_type = Code.APPLICATION_JSON
    template_name = Template.MANIFEST_JSON

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
    content_type = Code.APPLICATION_JS
    template_name = Template.SW_JS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        assets = []

        def appendWhen(path: str):
            return path.endswith(('.js', '.json', '.css', '.map', '.jpg', '.woff2', '.svg', '.png', '.jpeg')) and not (path.__contains__('/email/') or path.__contains__('/admin/'))
        assets = getDeepFilePaths(settings.STATIC_URL.strip('/'), appendWhen=appendWhen)

        assets.append(f"/{URL.OFFLINE}")
        assets.append(f"/{URL.MANIFEST}")

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
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LIVEDATA}"),
            ]),
            ignorelist=json.dumps([
                f"/{ADMINPATH}*",
                f"/{ADMINPATH}",
                f"/{URL.ROBOTS_TXT}",
                f"/{URL.REDIRECTOR}*",
                f"/{URL.AUTH}*",
                f"/{URL.MODERATION}*",
                f"/{URL.COMPETE}*",
                f"/{URL.LANDING}",
                f"/{URL.PROJECTS}{URL.Projects.ALLLICENSES}",
                f"/email/*",
                f"/{URL.MANAGEMENT}*",
                f"/{URL.MANAGEMENT}",
                setPathParams(f"/{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.People.SUCCESSORINVITE}"),
                setPathParams(f"/{URL.APPLANDING}"),
                setPathParams(f"/{URL.DOCTYPE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSES}"),
            ]),
            recacheList=json.dumps([
                f"/{URL.REDIRECTOR}*",
                f"/{URL.AUTH}*",
                setPathParams(f"/{URL.COMPETE}{URL.Compete.INVITEACTION}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILEEDIT}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ACCOUNTPREFERENCES}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILEEDIT}"),
            ]),
            netFirstList=json.dumps([
                f"{settings.MEDIA_URL}*",
                setPathParams(f"/{URL.BROWSER}"),
                f"/{URL.PROJECTS}{URL.Projects.NEWBIES}",
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE}"),
                f"/{URL.PEOPLE}{URL.People.NEWBIES}",
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILE}"),
            ])
        )))
        return context


@require_GET
def browser(request:WSGIRequest, type:str):
    try:
        if type == "new-profiles":
            excludeIDs = []
            if request.user.is_authenticated:
                excludeIDs.append(request.user.profile.getID())
            profiles = Profile.objects.exclude(id__in=excludeIDs).filter(
                suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[0:10]
            return peopleRendererstr(request, Template.People.BROWSE_NEWBIE, dict(profiles=profiles))
        elif type == "new-projects":
            projects = Project.objects.filter(
                status=Code.APPROVED).order_by('-approvedOn')[0:10]
            return projectsRendererstr(request, Template.Projects.BROWSE_NEWBIE, dict(projects=projects))
        else:
            return HttpResponseBadRequest()
    except:
        raise Http404()
