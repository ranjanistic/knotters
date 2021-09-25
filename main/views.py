import json
from itertools import chain
from django.utils import timezone
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from datetime import timedelta
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.utils.decorators import method_decorator
from allauth.account.decorators import verified_email_required
from django.core.cache import cache
from django.db.models import Q
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.shortcuts import redirect
from moderation.models import LocalStorage
from projects.models import FreeProject, LegalDoc, Project
from compete.models import Result
from people.models import Profile
from people.methods import rendererstr as peopleRendererstr
from projects.methods import rendererstr as projectsRendererstr
from compete.methods import rendererstr as competeRendererstr
from .env import ADMINPATH, ISPRODUCTION
from .methods import addMethodToAsyncQueue, errorLog, renderData, renderView, respondJson, verify_captcha
from .decorators import dev_only, github_only, require_JSON_body
from .methods import renderView, getDeepFilePaths
from .mailers import featureRelease
from .strings import Code, URL, setPathParams, Template, DOCS, COMPETE, PEOPLE, PROJECTS, Event
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
def docIndex(request: WSGIRequest) -> HttpResponse:
    docs = LegalDoc.objects.all()
    return renderView(request, Template.Docs.INDEX, fromApp=DOCS, data=dict(docs=docs))


@require_GET
def docs(request: WSGIRequest, type: str) -> HttpResponse:
    try:
        doc = LegalDoc.objects.get(pseudonym=type)
        return renderView(request, Template.Docs.DOC, fromApp=DOCS, data=dict(doc=doc))
    except Exception as e:
        try:
            return renderView(request, type, fromApp=DOCS)
        except Exception as e:
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


@require_JSON_body
def verifyCaptcha(request: WSGIRequest):
    try:
        capt_response = request.POST.get('g-recaptcha-response', False)
        if not capt_response:
            return respondJson(Code.NO)
        if verify_captcha(capt_response):
            return respondJson(Code.OK)
        return respondJson(Code.NO if ISPRODUCTION else Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO if ISPRODUCTION else Code.OK)

@csrf_exempt
@github_only
def githubEventsListener(request, type: str, event: str) -> HttpResponse:
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Invaild event type')
        ghevent = request.POST['ghevent']
        if event != ghevent:
            return HttpResponseBadRequest(f'event mismatch')

        if ghevent == Event.RELEASE:
            release = request.POST['release']
            action = request.POST.get('action', None)
            if action == Event.PUBLISHED:
                if not release['draft'] and release['name'] and release['body']:
                    addMethodToAsyncQueue(f'main.mailers.{featureRelease.__name__}',release['name'],release['body'])
        else:
            return HttpResponseBadRequest(ghevent)
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404()

@method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
class Robots(TemplateView):
    content_type = Code.TEXT_PLAIN
    template_name = Template.ROBOTS_TXT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = dict(**context, media=settings.MEDIA_URL)
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

        swassets, created = LocalStorage.objects.get_or_create(key=Code.SWASSETS, defaults=dict(
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
                f"/",
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
                setPathParams(f"/{URL.APPLANDING}"),
                setPathParams(f"/{URL.DOCS}{URL.Docs.TYPE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.SUCCESSORINVITE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.BROWSE_SEARCH}*"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_FREE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_MOD}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSES}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.BROWSE_SEARCH}*"),
            ]),
            recacheList=json.dumps([
                f"/{URL.REDIRECTOR}*",
                f"/{URL.AUTH}*",
                f"/{URL.SWITCH_LANG}setlang/",
                setPathParams(f"/{URL.COMPETE}{URL.Compete.INVITEACTION}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILEEDIT}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ACCOUNTPREFERENCES}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILEEDIT}"),
            ]),
            netFirstList=json.dumps([
                f"{settings.MEDIA_URL}*",
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_FREE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_MOD}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILE}"),
                setPathParams(f"/{URL.BROWSER}"),
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
                    createdOn__gte=(timezone.now()+timedelta(days=-15)),
                    suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[0:10]
            else:
                profiles = cache.get(
                    f"new_profiles_suggestion_{request.LANGUAGE_CODE}")
                if not profiles:
                    profiles = Profile.objects.filter(
                        createdOn__gte=(timezone.now()+timedelta(days=-15)),
                        suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[0:10]
                    cache.set(
                        f"new_profiles_suggestion_{request.LANGUAGE_CODE}", profiles, settings.CACHE_LONG)
            return peopleRendererstr(request, Template.People.BROWSE_NEWBIE, dict(profiles=profiles,count=len(profiles)))
        elif type == "new-projects":
            projects = Project.objects.filter(status=Code.APPROVED,approvedOn__gte=(timezone.now()+timedelta(days=-15))).order_by('-approvedOn','-createdOn')[0:5]
            projects = list(chain(projects,FreeProject.objects.filter(createdOn__gte=(timezone.now()+timedelta(days=-15))).order_by('-createdOn')[0:((10-len(projects)) or 1)]))
            return projectsRendererstr(request, Template.Projects.BROWSE_NEWBIE, dict(projects=projects,count=len(projects)))
        elif type == "recent-winners":
            results = cache.get(f"recent_winners_{request.LANGUAGE_CODE}")
            if not results:
                results = Result.objects.filter(competition__resultDeclared=True, competition__startAt__gte=(
                    timezone.now()+timedelta(days=-6))).order_by('-competition__endAt')[0:10]
                cache.set(
                    f"recent_winners_{request.LANGUAGE_CODE}", results, settings.CACHE_LONG)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_RECENT_WINNERS, dict(results=results,count=len(results))))
        elif type == "recommended-projects":
            query = Q()
            authquery = query
            if request.user.is_authenticated:
                query = Q(topics__in=request.user.profile.getTopics())
                authquery = ~Q(creator=request.user.profile)
            projects = list(chain(Project.objects.filter(Q(status=Code.APPROVED),authquery,query)[0:10],FreeProject.objects.filter(authquery,query)[0:10]))
            if(len(projects)<1):
                projects = list(chain(Project.objects.filter(Q(status=Code.APPROVED),authquery)[0:10],FreeProject.objects.filter(authquery)[0:10]))
            return projectsRendererstr(request, Template.Projects.BROWSE_RECOMMENDED, dict(projects=projects,count=len(projects)))
        elif type == "trending-topics":
            # TODO
            return HttpResponseBadRequest()
        elif type == "trending-projects":
            # TODO
            return HttpResponseBadRequest()
        elif type == "trending-profiles":
            # TODO
            return HttpResponseBadRequest()
        elif type == "newly-moderated":
            # TODO
            return HttpResponseBadRequest()
        elif type == "highest-month-xp-profiles":
            # TODO
            return HttpResponseBadRequest()
        else:
            return HttpResponseBadRequest()
    except Exception as e:
        print(e)
        raise Http404()
