from datetime import timedelta
from json import dumps as jsondumps
from json import loads as jsonloads
from os import path as ospath

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from compete.methods import competitionProfileData
from compete.methods import rendererstr as competeRendererstr
from compete.models import Competition, Result
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Q
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.utils.timezone import is_aware, make_aware
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from management.methods import competitionManagementRenderData, labelRenderData
from management.models import (GhMarketApp, GhMarketPlan, HookRecord,
                               ThirdPartyLicense)
from moderation.methods import moderationRenderData
from moderation.models import LocalStorage
from people.methods import profileRenderData
from people.methods import rendererstr as peopleRendererstr
from people.models import (CoreMember, DisplayMentor, GHMarketPurchase,
                           Profile, Topic)
from projects.methods import coreProfileData, freeProfileData
from projects.methods import rendererstr as projectsRendererstr
from projects.methods import verifiedProfileData
from projects.models import (BaseProject, CoreProject, FreeProject, LegalDoc,
                             Project, Snapshot)
from rjsmin import jsmin

from .bots import Github
from .decorators import (decode_JSON, dev_only, github_only,
                         normal_profile_required, require_JSON)
from .env import ADMINPATH, ISBETA, ISPRODUCTION
from .mailers import featureRelease
from .methods import (addMethodToAsyncQueue, errorLog, getDeepFilePaths,
                      renderData, renderString, renderView, respondJson,
                      respondRedirect, verify_captcha)
from .strings import (COMPETE, DOCS, MANAGEMENT, MODERATION, PEOPLE, PROJECTS,
                      URL, Browse, Code, Event, Message, Template,
                      setPathParams)


@require_GET
def offline(request: WSGIRequest) -> HttpResponse:
    return renderView(request, Template.OFFLINE)


@require_GET
def branding(request: WSGIRequest) -> HttpResponse:
    return renderView(request, Template.BRANDING)


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
    competition = cache.get('latest_competition', [])
    if not competition:
        competition = Competition.objects.filter(
            endAt__gt=timezone.now(), is_draft=False, resultDeclared=False
        ).order_by("-startAt").first()
        cache.set('latest_competition', competition, settings.CACHE_MICRO)
    if request.user.is_authenticated:
        if not request.user.profile.on_boarded:
            return respondRedirect(path=URL.ON_BOARDING)
        return renderView(request, Template.HOME, dict(competition=competition))
    topics = cache.get('homepage_topics', [])
    if not len(topics):
        topics = Topic.objects.filter()[:3]
        cache.set('homepage_topics', topics, settings.CACHE_LONG)
    project = cache.get('homepage_projects', None)
    if not project:
        project = BaseProject.objects.filter(creator=Profile.KNOTBOT(
        ), suspended=False, trashed=False).order_by("createdOn").first()
        cache.set('homepage_projects', project, settings.CACHE_LONG)
    return renderView(request, Template.INDEX, dict(topics=topics, project=project, competition=competition))


@require_GET
def home(request: WSGIRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect(URL.ROOT)
    competition = cache.get('latest_competition', [])
    if not competition:
        competition = Competition.objects.filter(
            endAt__gt=timezone.now(), is_draft=False, resultDeclared=False
        ).order_by("-startAt").first()
        cache.set('latest_competition', competition, settings.CACHE_MICRO)
    topics = cache.get('homepage_topics', [])
    if not len(topics):
        topics = Topic.objects.filter()[:3]
        cache.set('homepage_topics', topics, settings.CACHE_LONG)
    project = cache.get('homepage_project', None)
    if not project:
        project = BaseProject.objects.filter(creator=Profile.KNOTBOT(
        ), suspended=False, trashed=False).order_by("createdOn").first()
        cache.set('homepage_project', project, settings.CACHE_LONG)
    return renderView(request, Template.INDEX, dict(topics=topics, project=project, competition=competition))


@require_GET
def homeDomains(request: WSGIRequest, domain: str) -> HttpResponse:
    return renderView(request, domain, fromApp="home")


@require_GET
def redirector(request: WSGIRequest) -> HttpResponse:
    try:
        next = request.GET.get('n', '/')
        next = '/' if str(next).strip() == '' or not next or next == 'None' else next
        if next.startswith("/"):
            return redirect(next)
        else:
            return renderView(request, Template.FORWARD, dict(next=next))
    except:
        return redirect(URL.INDEX)


@require_GET
def at_nickname(request: WSGIRequest, nickname) -> HttpResponse:
    try:
        if nickname == "me":
            if not request.user.is_authenticated:
                return redirect(URL.Auth.LOGIN)
            return redirect(request.user.profile.get_link)
        profile = Profile.objects.get(nickname=nickname)
        return redirect(profile.get_link)
    except Exception as e:
        raise Http404(e)


@require_GET
def at_emoji(request: WSGIRequest, emoticon) -> HttpResponse:
    try:
        profile = Profile.objects.get(emoticon=emoticon)
        return redirect(profile.get_link)
    except:
        raise Http404()


@normal_profile_required
@require_GET
def on_boarding(request: WSGIRequest) -> HttpResponse:
    try:
        return renderView(request, Template.ON_BOARDING)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@decode_JSON
def on_boarding_update(request: WSGIRequest) -> HttpResponse:
    try:
        on_boarded = request.POST.get('onboarded', False)
        if on_boarded and not (request.user.profile.on_boarded and request.user.profile.xp > 9):
            request.user.profile.increaseXP(10)
        request.user.profile.on_boarded = on_boarded == True
        request.user.profile.save()
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


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
            tpls = []
            if type == 'osl':
                tpls = ThirdPartyLicense.objects.filter().order_by("title")
            return renderView(request, type, fromApp=DOCS, data=dict(tpls=tpls))
        except Exception as e:
            raise Http404()


@require_GET
def landing(request: WSGIRequest) -> HttpResponse:
    apps = cache.get('gh_market_apps', [])
    if not len(apps):
        apps = GhMarketApp.objects.filter()
        cache.set('gh_market_apps', apps, settings.CACHE_SHORT)
    return renderView(request, Template.LANDING, dict(
        gh_market_app=apps.first()
    ))


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


@require_GET
def fameWall(request: WSGIRequest):
    return renderView(request, Template.FAME_WALL)


@require_JSON
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


@require_GET
def snapshot(request: WSGIRequest, snapID):
    try:
        snapshot = Snapshot.objects.get(id=snapID)
        return renderView(request, Template.VIEW_SNAPSHOT, dict(snapshot=snapshot))
    except ObjectDoesNotExist as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@decode_JSON
def donation(request: WSGIRequest):
    if request.method == "POST":
        return respondJson(Code.OK)
    else:
        return renderView(request, Template.DONATION)


@require_GET
@cache_control(no_cache=True, public=True, max_age=settings.CACHE_MINI)
def scripts(request, script):
    if script not in Template.script.getScriptTemplates():
        raise Http404("Script not found")
    stringrender = render_to_string(script, request=request, context=renderData(
        fromApp=request.GET.get('fromApp', '')))
    if not settings.DEBUG:
        stringrender = jsmin(stringrender)
    return HttpResponse(stringrender, content_type=Code.APPLICATION_JS)


@require_GET
@cache_control(no_cache=True, public=True, max_age=settings.CACHE_MINI)
def scripts_subapp(request, subapp: str, script: str):
    if script not in Template.script.getScriptTemplates():
        raise Http404("Script not found")
    data = dict()
    if subapp == PROJECTS:
        projectID = request.GET.get('id', None)
        if script == Template.Script.ZERO:
            data = freeProfileData(request, projectID=projectID)
        elif script == Template.Script.ONE:
            data = verifiedProfileData(request, projectID=projectID)
        elif script == Template.Script.TWO:
            data = coreProfileData(request, projectID=projectID)
    elif subapp == COMPETE:
        compID = request.GET.get('id', None)
        if script == Template.Script.PROFILE:
            data = competitionProfileData(request, compID=compID)
    elif subapp == MANAGEMENT:
        labelID = request.GET.get("id", None)
        if script == Template.Script.TOPIC:
            data = labelRenderData(request, Code.TOPIC, labelID)
        elif script == Template.Script.CATEGORY:
            data = labelRenderData(request, Code.CATEGORY, labelID)
        elif script == Template.Script.COMPETE:
            data = competitionManagementRenderData(request, compID=labelID)
    elif subapp == MODERATION:
        modID = request.GET.get("id", None)
        data = moderationRenderData(request, modID)
    elif subapp == PEOPLE:
        userID = request.GET.get('id', None)
        if script == Template.Script.PROFILE:
            data = profileRenderData(request, userID=userID)
    stringrender = render_to_string(f"{subapp}/scripts/{script}", request=request,
                                    context=renderData(fromApp=request.GET.get('fromApp', subapp), data=data))
    if not settings.DEBUG:
        stringrender = jsmin(stringrender)
    return HttpResponse(stringrender, content_type=Code.APPLICATION_JS)


def handler403(request, exception, template_name="403.html"):
    response = render(template_name)
    response.status_code = 403
    return response


@csrf_exempt
@github_only
def githubEventsListener(request, type: str, targetID: str) -> HttpResponse:
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Only hook events supported')

        hookID = request.POST['hookID']
        ghevent = request.POST['ghevent']

        hookrecord, _ = HookRecord.objects.get_or_create(hookID=hookID, defaults=dict(
            success=False
        ))
        if hookrecord.success:
            return HttpResponse(Code.NO)

        if ghevent == Event.RELEASE:
            return HttpResponse(Code.UNKNOWN_EVENT)
            release = request.POST['release']
            action = request.POST.get('action', None)
            if action == Event.PUBLISHED:
                if not release['draft'] and release['name'] and release['body']:
                    addMethodToAsyncQueue(
                        f'main.mailers.{featureRelease.__name__}', release['name'], release['body'])

        elif ghevent == Event.MARKETPLACE_PURCHASE:
            action = request.POST.get('action', None)
            if not action:
                raise Exception(ghevent)
            effective_date = parse_datetime(request.POST['effective_date'])
            if not is_aware(effective_date):
                try:
                    effective_date = make_aware(effective_date)
                except:
                    pass
            sender = request.POST['sender']
            m_purchase = request.POST['marketplace_purchase']
            next_billing_date = parse_datetime(m_purchase['next_billing_date'])
            if not is_aware(next_billing_date):
                try:
                    next_billing_date = make_aware(next_billing_date)
                except:
                    pass
            account = m_purchase['account']
            if account['type'] == "Organization":
                used_email = account['organization_billing_email']
            else:
                user_gh_id = account["id"]
                ghsocial = SocialAccount.objects.get(
                    provider=GitHubProvider.id, uid=user_gh_id)
                if not ghsocial:
                    ghUser = Github.get_user_by_id(int(user_gh_id))
                    used_email = ghUser.email
                else:
                    used_email = ghsocial.extra_data['email']

            billcycle = m_purchase['billing_cycle']
            unit_count = m_purchase['unit_count']

            p_id = m_purchase['plan']['id']
            gh_plan = GhMarketPlan.objects.get(
                gh_app__gh_id=targetID, gh_id=p_id)
            emailaddr = EmailAddress.objects.filter(email=used_email).first()

            if action == "purchased":
                if emailaddr:
                    GHMarketPurchase.objects.create(
                        profile=emailaddr.user.profile,
                        effective_date=effective_date,
                        gh_app_plan=gh_plan,
                        units_purchased=(unit_count or 1)
                    )
                else:
                    GHMarketPurchase.objects.create(
                        email=used_email,
                        effective_date=effective_date,
                        gh_app_plan=gh_plan,
                        units_purchased=(unit_count or 1)
                    )

            elif action == "changed":
                pre_m_purchase = request.POST['previous_marketplace_purchase']

                pre_account = pre_m_purchase['account']
                if pre_account['type'] == "Organization":
                    pre_used_email = pre_account['organization_billing_email']
                else:
                    pre_user_gh_id = pre_account["id"]
                    pre_ghsocial = SocialAccount.objects.get(
                        provider=GitHubProvider.id, uid=pre_user_gh_id)
                    if not ghsocial:
                        pre_ghUser = Github.get_user_by_id(int(pre_user_gh_id))
                        pre_used_email = pre_ghUser.email
                    else:
                        pre_used_email = pre_ghsocial.extra_data['email']

                pre_p_id = pre_m_purchase['plan']['id']
                pre_gh_plan = GhMarketPlan.objects.get(
                    gh_app__gh_id=targetID, gh_id=pre_p_id)
                pre_emailaddr = EmailAddress.objects.filter(
                    email=pre_used_email).first()
                if pre_emailaddr:
                    pre_GHMarketPurchase = GHMarketPurchase.objects.filter(
                        profile=pre_emailaddr.user.profile,
                        gh_app_plan=pre_gh_plan
                    ).first()
                else:
                    pre_GHMarketPurchase = GHMarketPurchase.objects.filter(
                        email=pre_used_email,
                        gh_app_plan=pre_gh_plan
                    ).first()
                if pre_GHMarketPurchase:
                    pre_GHMarketPurchase.gh_app_plan = gh_plan
                    pre_GHMarketPurchase.effective_date = effective_date
                    pre_GHMarketPurchase.next_billing_date = next_billing_date
                    pre_GHMarketPurchase.units_purchased = (unit_count or 1)
                    if emailaddr:
                        pre_GHMarketPurchase.profile = emailaddr.user.profile
                    pre_GHMarketPurchase.save()
                else:
                    if emailaddr:
                        GHMarketPurchase.objects.create(
                            profile=emailaddr.user.profile,
                            effective_date=effective_date,
                            gh_app_plan=gh_plan,
                            next_billing_date=next_billing_date,
                            units_purchased=(unit_count or 1)
                        )
                    else:
                        GHMarketPurchase.objects.create(
                            email=used_email,
                            effective_date=effective_date,
                            gh_app_plan=gh_plan,
                            next_billing_date=next_billing_date,
                            units_purchased=(unit_count or 1)
                        )

            elif action == "cancelled":
                if emailaddr:
                    gHMarketPurchase = GHMarketPurchase.objects.filter(
                        profile=emailaddr.user.profile,
                        gh_app_plan=gh_plan
                    ).first()
                else:
                    gHMarketPurchase = GHMarketPurchase.objects.filter(
                        email=used_email,
                        gh_app_plan=gh_plan
                    ).first()
                if gHMarketPurchase:
                    gHMarketPurchase.delete()

            elif action == "pending_change":
                pass
            elif action == "pending_change_cancelled":
                pass
            else:
                return HttpResponseBadRequest(action)
        else:
            return HttpResponseBadRequest(ghevent)
        hookrecord.success = True
        hookrecord.save()
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404()


# @method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
class Robots(TemplateView):
    content_type = Code.TEXT_PLAIN
    template_name = Template.ROBOTS_TXT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cacheKey = f"{Template.ROBOTS_TXT}_suspended_list"
        suspended = cache.get(cacheKey, [])
        if not len(suspended):
            suspended = Profile.objects.filter(
                Q(suspended=True) | Q(is_zombie=True))
            cache.set(cacheKey, suspended, settings.CACHE_SHORT)
        context = dict(**context, media=settings.MEDIA_URL,
                       suspended=suspended, ISBETA=ISBETA)
        return context


@method_decorator(cache_page(settings.CACHE_SHORT), name='dispatch')
class Sitemap(TemplateView):
    content_type = Code.APPLICATION_XML
    template_name = Template.SITEMAP

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cacheKey = f"sitemap_content_links"
        LINKS = cache.get(cacheKey, [])
        if not len(LINKS):
            def FILTER(u): return "*" not in u and not u.startswith(
                "http") and not u.endswith(('.png', '.svg', '.webp'))
            ROOTS = list(filter(FILTER, URL().getURLSForClient().values()))
            PROJECTS = list(
                filter(FILTER, URL.projects.getURLSForClient().values()))
            COMPETE = list(
                filter(FILTER, URL.compete.getURLSForClient().values()))
            COMMUNITY = list(
                filter(FILTER, URL.people.getURLSForClient().values()))
            AUTH = list(filter(FILTER, URL.auth.getURLSForClient().values()))
            MGM = list(
                filter(FILTER, URL.management.getURLSForClient().values()))
            LINKS = [ROOTS, PROJECTS, COMPETE, COMMUNITY, AUTH, MGM]
            cache.set(cacheKey, LINKS, settings.CACHE_LONGER)
        context = dict(**context,
                       media=settings.MEDIA_URL,
                       LINKS=LINKS
                       )
        return context


# @method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
class Manifest(TemplateView):
    content_type = Code.APPLICATION_JSON
    template_name = Template.MANIFEST_JSON

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        stringrender = render_to_string(
            self.get_template_names(), request=self.request, context=context)
        try:
            if not settings.DEBUG:
                stringrender = jsondumps(
                    jsonloads(stringrender), separators=(',', ':'))
        except:
            pass
        return HttpResponse(stringrender, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sizes = []

        def appendWhen(path: str):
            condition = path.endswith(
                ('icon-circle.webp', 'icon-square.webp', 'icon-circle.png', 'icon-square.png'))
            if condition:
                parts = path.split('/')
                size = int(parts[len(parts)-2])
                sizes.append(size)
            return condition
        assets = getDeepFilePaths(ospath.join(
            settings.STATIC_ROOT, 'graphics/self'), appendWhen=appendWhen)
        assets = list(map(lambda p: str(
            p.replace(settings.STATIC_ROOT, settings.STATIC_URL)), assets))

        icons = []

        for i in range(len(assets)):
            icons.append(dict(
                src=assets[i],
                size=f"{sizes[i]}x{sizes[i]}",
                type=assets[i].split('.')[-1],
            ))

        context = dict(**context, icons=icons)
        return context


class ServiceWorker(TemplateView):
    content_type = Code.APPLICATION_JS
    template_name = Template.SW_JS

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.setdefault('content_type', self.content_type)
        stringrender = render_to_string(
            self.get_template_names(), request=self.request, context=context)
        try:
            if not settings.DEBUG:
                stringrender = jsmin(stringrender)
        except:
            pass
        return HttpResponse(stringrender, **response_kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        assets = []

        def appendWhen(path: str):
            return path.endswith(('.js', '.css', '.map', '.jpg', '.webp', '.woff2', '.svg', '.png', '.jpeg')) and not (path.__contains__('/email/') or path.__contains__('/admin/'))
        assets = getDeepFilePaths(
            "static", appendWhen=appendWhen)

        def attachStaticURL(path: str):
            return str(path.replace("/static/", settings.STATIC_URL))

        assets = list(map(attachStaticURL, assets))
        assets.append(f"/{URL.OFFLINE}")
        assets.append(f"/{URL.MANIFEST}")

        cacheKey = f'localstore_{Code.SWASSETS}'
        swassets = cache.get(cacheKey, None)
        created = False
        if not swassets:
            swassets, created = LocalStorage.objects.get_or_create(key=Code.SWASSETS, defaults=dict(
                value=jsondumps(assets)
            ))
        if not created:
            oldassets = jsonloads(swassets.value)
            different = False
            if len(oldassets) != len(assets):
                different = True
            else:
                for old in oldassets:
                    if not old in assets:
                        different = True
                        break
                if not different:
                    for new in assets:
                        if not new in oldassets:
                            different = True
                            break

            assets = assets if different else oldassets
            if different:
                swassets.value = jsondumps(assets)
                swassets.save()
                cache.set(cacheKey, swassets)
            else:
                assets = oldassets

        context = dict(**context, **renderData(dict(
            OFFLINE=f"/{URL.OFFLINE}",
            assets=jsondumps(assets),
            noOfflineList=jsondumps([
                setPathParams(f"/{URL.ON_BOARDING}"),
                setPathParams(
                    f"/{URL.COMPETE}{URL.Compete.COMPETETABSECTION}"),
                setPathParams(f"/{URL.COMPETE}{URL.Compete.INDEXTAB}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.SETTINGTAB}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILETAB}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LIVEDATA}"),
            ]),
            ignorelist=jsondumps([
                f"/{ADMINPATH}*",
                f"/{ADMINPATH}",
                f"/{URL.WEBPUSH}*",
                f"/{URL.ROBOTS_TXT}",
                f"/{URL.SITEMAP}",
                f"/{URL.VERSION_TXT}",
                f"/{URL.REDIRECTOR}",
                f"/{URL.AUTH}",
                f"/{URL.AUTH}*",
                f"/{URL.MODERATION}*",
                f"/{URL.COMPETE}*",
                f"/{URL.PROJECTS}{URL.Projects.ALLLICENSES}",
                f"/email/*",
                f"/{URL.MANAGEMENT}*",
                f"/{URL.MANAGEMENT}",
                setPathParams(f"/{URL.APPLANDING}"),
                setPathParams(f"/{URL.DOCS}{URL.Docs.TYPE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.Auth.SUCCESSORINVITE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ZOMBIE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.PROJECT_TRANS_INVITE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.VIEW_COCREATOR_INVITE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.VER_MOD_TRANS_INVITE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.CORE_MOD_TRANS_INVITE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.VER_DEL_REQUEST}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.CORE_DEL_REQUEST}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_FREE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_MOD}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_CORE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSES}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.CREATE_FRAME}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.REPORT_CATEGORIES}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.REPORT_CATEGORIES}"),
            ]),
            recacheList=jsondumps([
                f"/{URL.REDIRECTOR}",
            ]),
            netFirstList=jsondumps([
                f"/{URL.LANDING}",
                f"/{URL.FAME_WALL}",
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_MOD}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_CORE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_FREE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.ADMIRATIONS}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.SNAP_ADMIRATIONS}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILETAB}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.FRAMEWORK}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.BROWSE_SEARCH}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.BROWSE_SEARCH}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSE_SEARCH}"),
                setPathParams(f"/{URL.VIEW_SNAPSHOT}"),
                setPathParams(f"/{URL.BRANDING}"),
                setPathParams(f"/{URL.BROWSER}"),
                setPathParams(f"/{URL.SCRIPTS}"),
                setPathParams(f"/{URL.SCRIPTS_SUBAPP}"),
            ])
        )))
        return context


class Version(TemplateView):
    content_type = Code.TEXT_PLAIN
    template_name = Template.VERSION

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@decode_JSON
def browser(request: WSGIRequest, type: str):
    try:
        cachekey = f"main_browser_{type}{request.LANGUAGE_CODE}"
        excludeUserIDs = []
        if request.user.is_authenticated:
            excludeUserIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}{request.user.id}"

        limit = int(request.POST.get('limit', request.GET.get('limit', 10)))
        if type == Browse.PROJECT_SNAPSHOTS:
            if request.user.is_authenticated:
                excludeIDs = request.POST.get('excludeIDs', [])
                limit = int(request.POST.get(
                    'limit', request.GET.get('limit', 5)))
                cachekey = f"{cachekey}{limit}"
                if len(excludeIDs):
                    cachekey = cachekey + "".join(excludeIDs)
                snaps = cache.get(cachekey, [])
                snapIDs = [snap.id for snap in snaps]

                if not len(snaps):
                    snaps = Snapshot.objects.filter(Q(Q(base_project__admirers=request.user.profile) | Q(base_project__creator=request.user.profile) | Q(creator__admirers=request.user.profile)),
                                                    base_project__suspended=False, base_project__trashed=False, suspended=False).exclude(id__in=excludeIDs).exclude(creator__user__id__in=excludeUserIDs).distinct().order_by("-created_on")[:limit]
                    snapIDs = [snap.id for snap in snaps]
                    cache.set(cachekey, snaps, settings.CACHE_INSTANT)

                data = dict(
                    html=renderString(
                        request, Template.SNAPSHOTS, dict(snaps=snaps)),
                    snapIDs=snapIDs,
                    recommended=False
                )
                return respondJson(Code.OK, data)
            else:
                return respondJson(Code.OK, dict(snapIDs=[]))
        elif type == Browse.NEW_PROFILES:
            profiles = cache.get(cachekey, [])
            if not len(profiles):
                if request.user.is_authenticated:
                    excludeUserIDs.append(request.user.profile.getUserID())
                profiles = Profile.objects.exclude(user__id__in=excludeUserIDs).filter(
                    user__emailaddress__verified=True,
                    createdOn__gte=(
                        timezone.now()+timedelta(days=-60)),
                    suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[:limit]
                cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_NEWBIE, dict(profiles=profiles, count=len(profiles)))

        elif type == Browse.NEW_PROJECTS:
            projects = cache.get(cachekey, [])
            if not len(projects):
                projects = BaseProject.objects.filter(createdOn__gte=(
                    timezone.now()+timedelta(days=-30)), suspended=False, trashed=False).exclude(creator__user__id__in=excludeUserIDs).order_by('-createdOn')[:limit]

                projects = list(
                    set(list(filter(lambda p: p.is_approved, projects))))
                cache.set(cachekey, projects, settings.CACHE_MINI)

            return projectsRendererstr(request, Template.Projects.BROWSE_NEWBIE, dict(projects=projects, count=len(projects)))

        elif type == Browse.RECENT_WINNERS:
            results = cache.get(cachekey, None)
            if results is None:
                results = Result.objects.filter(competition__resultDeclared=True, competition__startAt__gte=(
                    timezone.now()+timedelta(days=-6))).order_by('-competition__endAt')[:limit]
                cache.set(cachekey, results, settings.CACHE_MINI)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_RECENT_WINNERS, dict(results=results, count=len(results))))

        elif type == Browse.RECOMMENDED_PROJECTS:
            projects = cache.get(cachekey, [])
            count = len(projects)
            if not count:
                query = Q()
                authquery = query
                if request.user.is_authenticated:
                    query = Q(topics__in=request.user.profile.getTopics())
                    authquery = ~Q(creator=request.user.profile)

                projects = BaseProject.objects.filter(Q(trashed=False, suspended=False), authquery, query).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit]
                projects = list(
                    set(list(filter(lambda p: p.is_approved, projects))))
                count = len(projects)
                if count < 1:
                    projects = BaseProject.objects.filter(Q(trashed=False, suspended=False), authquery).exclude(
                        creator__user__id__in=excludeUserIDs)[:limit]
                    projects = list(
                        set(list(filter(lambda p: p.is_approved, projects))))
                    count = len(projects)

                if count:
                    cache.set(cachekey, projects, settings.CACHE_MINI)

            return projectsRendererstr(request, Template.Projects.BROWSE_RECOMMENDED, dict(projects=projects, count=count))
        elif type == Browse.TRENDING_TOPICS:
            # TODO
            pass
        elif type == Browse.TRENDING_PROJECTS:
            projects = cache.get(cachekey, [])
            if not len(projects):
                projects = BaseProject.objects.filter(Q(trashed=False, suspended=False)).exclude(
                    creator__user__id__in=excludeUserIDs).annotate(num_admirers=Count('admirers')).order_by('-num_admirers')[:limit]
                projects = list(
                    set(list(filter(lambda p: p.is_approved, projects))))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_PROFILES:
            profiles = cache.get(cachekey, [])
            if not len(profiles):
                profiles = Profile.objects.filter(
                    Q(suspended=False, to_be_zombie=False, is_active=True)).exclude(
                        user__id__in=excludeUserIDs
                ).annotate(num_admirers=Count('admirers')).order_by('-num_admirers')[:limit]
                cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING, dict(profiles=profiles, count=len(profiles)))
        elif type == Browse.NEWLY_MODERATED:
            projects = cache.get(cachekey, [])
            if not len(projects):
                vids = Project.objects.filter(status=Code.APPROVED, trashed=False, suspended=False, approvedOn__gte=timezone.now()+timedelta(days=-60)).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit].values_list("id", flat=True)
                cids = CoreProject.objects.filter(status=Code.APPROVED, trashed=False, suspended=False, approvedOn__gte=timezone.now()+timedelta(days=-60)).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit].values_list("id", flat=True)
                projects = BaseProject.objects.filter(
                    id__in=list(cids)+list(vids))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_NEWLY_MODERATED, dict(projects=projects, count=len(projects)))
        elif type == Browse.HIGHEST_MONTH_XP_PROFILES:
            profiles = cache.get(cachekey, [])
            if not len(profiles):
                profiles = Profile.objects.filter(
                    Q(suspended=False, to_be_zombie=False, is_active=True)).exclude(
                        user__id__in=excludeUserIDs
                ).order_by('-xp')[:limit]
                cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_HIGHEST_MONTH_XP_PROFILES, dict(profiles=profiles, count=len(profiles)))
        elif type == Browse.LATEST_COMPETITIONS:
            competitions = cache.get(cachekey, [])
            if not len(competitions):
                competitions = Competition.objects.filter(
                    hidden=False, is_draft=False).order_by("-startAt")[:limit]
                cache.set(cachekey, competitions, settings.CACHE_MINI)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_LATEST_COMP, dict(competitions=competitions, count=len(competitions))))
        elif type == Browse.TRENDING_MENTORS:
            mentors = cache.get(cachekey, [])
            if not len(mentors):
                mentors = Profile.objects.filter(
                    is_mentor=True, suspended=False, is_active=True, to_be_zombie=False).order_by("-xp")[:limit]
                if request.user.is_authenticated:
                    mentors = request.user.profile.filterBlockedProfiles(
                        mentors)
                cache.set(cachekey, mentors, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING_MENTORS, dict(mentors=mentors, count=len(mentors)))
        elif type == Browse.TRENDING_MODERATORS:
            moderators = cache.get(cachekey, [])
            if not len(moderators):
                moderators = Profile.objects.filter(
                    is_moderator=True, suspended=False, is_active=True, to_be_zombie=False).order_by("-xp")[:limit]
                if request.user.is_authenticated:
                    moderators = request.user.profile.filterBlockedProfiles(
                        moderators)
                cache.set(cachekey, moderators, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING_MODS, dict(moderators=moderators, count=len(moderators)))
        elif type == Browse.DISPLAY_MENTORS:
            dmentors = cache.get(cachekey, [])
            count = len(dmentors)
            if not count:
                dmentors = DisplayMentor.objects.filter(
                    hidden=False).order_by("-createdOn")
                count = len(dmentors)
                if count:
                    cache.set(cachekey, dmentors, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_DISPLAY_MENTORS, dict(dmentors=dmentors, count=count))
        elif type == Browse.CORE_MEMBERS:
            coremems = cache.get(cachekey, [])
            count = len(coremems)
            if not count:
                coremems = CoreMember.objects.filter(hidden=False)
                count = len(coremems)
                if count:
                    cache.set(cachekey, coremems, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_CORE_MEMBERS, dict(coremems=coremems, count=count))
        elif type == Browse.TOPIC_PROJECTS:
            if request.user.is_authenticated:
                projects = cache.get(cachekey, [])
                tcacheKey = f"{cachekey}_topic"
                topic = cache.get(tcacheKey, None)
                if not topic or not len(projects):
                    if request.user.profile.totalAllTopics():
                        topic = request.user.profile.getAllTopics()[0]
                    else:
                        topic = request.user.profile.recommended_topics()[0]
                    projects = BaseProject.objects.filter(trashed=False, suspended=False, topics=topic).exclude(
                        creator__user__id__in=excludeUserIDs)[:limit]
                    projects = list(
                        set(list(filter(lambda p: p.is_approved, projects))))
                    cache.set(cachekey, projects, settings.CACHE_MINI)
                    cache.set(tcacheKey, topic, settings.CACHE_MINI)
                return projectsRendererstr(request, Template.Projects.BROWSE_TOPIC_PROJECTS, dict(projects=projects, count=len(projects), topic=topic))
            else:
                pass
        elif type == Browse.TOPIC_PROFILES:
            if request.user.is_authenticated:
                profiles = cache.get(cachekey, [])
                tcacheKey = f"{cachekey}_topic"
                topic = cache.get(tcacheKey, None)
                if not topic or not len(profiles):
                    if request.user.profile.totalAllTopics():
                        topic = request.user.profile.getAllTopics()[0]
                    else:
                        topic = request.user.profile.recommended_topics()[0]
                    profiles = Profile.objects.filter(suspended=False, is_active=True, to_be_zombie=False, topics=topic).exclude(
                        user__id__in=excludeUserIDs)[:limit]
                    cache.set(cachekey, profiles, settings.CACHE_MINI)
                    cache.set(tcacheKey, topic, settings.CACHE_MINI)
                return peopleRendererstr(request, Template.People.BROWSE_TOPIC_PROFILES, dict(profiles=profiles, count=len(profiles), topic=topic))
            else:
                pass
        elif type == Browse.TRENDING_CORE:
            projects = cache.get(cachekey, [])
            if not len(projects):
                projects = CoreProject.objects.filter(Q(trashed=False, suspended=False)).exclude(
                    creator__user__id__in=excludeUserIDs, status=Code.APPROVED).annotate(num_admirers=Count('admirers')).order_by('-num_admirers')[:limit]
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING_CORE, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_VERIFIED:
            projects = cache.get(cachekey, [])
            if not len(projects):
                projects = Project.objects.filter(Q(trashed=False, suspended=False)).exclude(
                    creator__user__id__in=excludeUserIDs, status=Code.APPROVED).annotate(num_admirers=Count('admirers')).order_by('-num_admirers')[:limit]
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING_VERIFIED, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_QUICK:
            projects = cache.get(cachekey, [])
            if not len(projects):
                projects = FreeProject.objects.filter(Q(trashed=False, suspended=False)).exclude(
                    creator__user__id__in=excludeUserIDs).annotate(num_admirers=Count('admirers')).order_by('-num_admirers')[:limit]
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING_QUICK, dict(projects=projects, count=len(projects)))
        else:
            return HttpResponseBadRequest(type)
        return HttpResponse()
    except Exception as e:
        errorLog(e)
        if request.POST.get(Code.JSON_BODY, False):
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)
