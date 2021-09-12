import json
from django.utils import timezone
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from datetime import timedelta
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.shortcuts import redirect
from moderation.models import LocalStorage
from projects.models import LegalDoc, Project
from compete.models import Competition, Result
from people.models import Profile
from people.methods import rendererstr as peopleRendererstr
from projects.methods import rendererstr as projectsRendererstr
from compete.methods import rendererstr as competeRendererstr
from .env import ADMINPATH
from .methods import errorLog, renderData, renderView, respondJson, verify_captcha
from .decorators import dev_only, require_JSON_body
from .methods import renderView, getDeepFilePaths
from .strings import Code, URL, setPathParams, Template, DOCS, COMPETE, PEOPLE, PROJECTS
from django_q.tasks import async_task


@require_GET
@cache_page(settings.CACHE_LONG)
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
# @cache_page(settings.CACHE_SHORT)
def index(request: WSGIRequest) -> HttpResponse:
    
    # comp = Competition.objects.filter(
    #     startAt__lt=timezone.now(), endAt__gte=timezone.now()).order_by('-createdOn').first()
    # data = dict(
    #     alerts=alerts
    # )
    return renderView(request, Template.INDEX)


@require_GET
def redirector(request: WSGIRequest) -> HttpResponse:
    next = request.GET.get('n', '/')
    next = '/' if str(next).strip() == '' or not next or next == 'None' else next
    if next.startswith("/"):
        return redirect(next)
    else:
        return renderView(request, Template.FORWARD, dict(next=next))


@require_GET
# @cache_page(settings.CACHE_LONG)
def docIndex(request: WSGIRequest) -> HttpResponse:
    docs = LegalDoc.objects.all()
    return renderView(request, Template.Docs.INDEX, fromApp=DOCS, data=dict(docs=docs))


@require_GET
# @cache_page(settings.CACHE_LONG)
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
# @cache_page(settings.CACHE_SHORT)
def landing(request: WSGIRequest) -> HttpResponse:
    return renderView(request, Template.LANDING)


@require_GET
# @cache_page(settings.CACHE_SHORT)
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


@method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
class Robots(TemplateView):
    content_type = Code.TEXT_PLAIN
    template_name = Template.ROBOTS_TXT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context = dict(**context,static=settings.STATIC_URL, media=settings.MEDIA_URL)
        return context


@method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
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


# @method_decorator(cache_page(settings.CACHE_SHORT), name='dispatch')
class ServiceWorker(TemplateView):
    content_type = Code.APPLICATION_JS
    template_name = Template.SW_JS

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        assets = []

        def appendWhen(path: str):
            return path.endswith(('.js', '.css', '.map', '.jpg', '.woff2', '.svg', '.png', '.jpeg')) and not (path.__contains__('/email/') or path.__contains__('/admin/'))
        assets = getDeepFilePaths(
            settings.STATIC_URL.strip('/'), appendWhen=appendWhen)

        assets.append(f"/{URL.OFFLINE}")
        assets.append(f"/{URL.MANIFEST}")

        swassets,created = LocalStorage.objects.get_or_create(key=Code.SWASSETS, defaults=dict(
            value=json.dumps(assets)
        ))
        if not created:
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
            else:
                assets = oldassets

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
def browser(request: WSGIRequest, type: str):
    try:
        if type == "new-profiles":
            excludeIDs = []
            if request.user.is_authenticated:
                excludeIDs.append(request.user.profile.getUserID())
                excludeIDs += request.user.profile.blockedIDs
                profiles = Profile.objects.exclude(user__id__in=excludeIDs).filter(
                    suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[0:10]
            else:
                profiles = cache.get(f"new_profiles_suggestion_{request.LANGUAGE_CODE}")
                if not profiles:
                    profiles = Profile.objects.filter(
                        suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[0:10]
                    cache.set(f"new_profiles_suggestion_{request.LANGUAGE_CODE}", profiles, settings.CACHE_LONG)
            return peopleRendererstr(request, Template.People.BROWSE_NEWBIE, dict(profiles=profiles))
        elif type == "new-projects":
            projects = Project.objects.filter(
                status=Code.APPROVED).order_by('-approvedOn')[0:10]
            return projectsRendererstr(request, Template.Projects.BROWSE_NEWBIE, dict(projects=projects))
        elif type == "recent-winners":
            results = cache.get(f"recent_winners_{request.LANGUAGE_CODE}")
            if not results:
                results = Result.objects.filter(competition__resultDeclared=True,competition__startAt__gte=(timezone.now()+timedelta(days=-6))).order_by('-competition__endAt')[0:10]
                cache.set(f"recent_winners_{request.LANGUAGE_CODE}", results, settings.CACHE_LONG)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_RECENT_WINNERS, dict(results=results)))
        else:
            return HttpResponseBadRequest()
    except Exception as e:
        print(e)
        raise Http404()


@require_JSON_body
def verifyCaptcha(request: WSGIRequest):
    try:
        capt_response = request.POST.get('g-recaptcha-response', False)
        if not capt_response:
            return respondJson(Code.NO)
        if verify_captcha(capt_response):
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)
