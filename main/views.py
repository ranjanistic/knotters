import json
from django.core.exceptions import ObjectDoesNotExist
from django.template.loader import render_to_string
from rjsmin import jsmin
from django.utils import timezone
from django.core.handlers.wsgi import WSGIRequest
from django.views.generic import TemplateView
from datetime import timedelta
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.github.provider import GitHubProvider
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.utils.decorators import method_decorator
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware
from django.core.cache import cache
from django.db.models import Q
from django.conf import settings
from django.views.decorators.cache import cache_page
from django.shortcuts import redirect, render
from management.models import HookRecord, GhMarketPlan, GhMarketApp
from moderation.models import LocalStorage
from projects.models import BaseProject, LegalDoc, Snapshot
from compete.models import Result, Competition
from people.models import DisplayMentor, Profile, GHMarketPurchase
from people.methods import rendererstr as peopleRendererstr
from projects.methods import rendererstr as projectsRendererstr
from compete.methods import rendererstr as competeRendererstr
from .bots import Github
from .env import ADMINPATH, ISPRODUCTION, ISBETA
from .methods import addMethodToAsyncQueue, errorLog, getDeepFilePaths, renderData, renderView, respondJson, respondRedirect, verify_captcha, renderString
from .decorators import dev_only, github_only, normal_profile_required, require_JSON_body, decode_JSON
from .mailers import featureRelease
from .strings import Code, URL, Message, setPathParams, Template, Browse, DOCS, COMPETE, PEOPLE, PROJECTS, Event


@require_GET
@cache_page(settings.CACHE_LONG)
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
    if request.user.is_authenticated and not request.user.profile.on_boarded:
        return respondRedirect(path=URL.ON_BOARDING)
    competition = Competition.objects.filter(endAt__gt=timezone.now(),is_draft=False,resultDeclared=False).order_by("-startAt").first()
    return renderView(request, Template.INDEX, dict(competition=competition))


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

@normal_profile_required
@require_GET
def on_boarding(request:WSGIRequest) -> HttpResponse:
    try:
        return renderView(request, Template.ON_BOARDING)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@normal_profile_required
@require_POST
@decode_JSON
def on_boarding_update(request:WSGIRequest) -> HttpResponse:
    try:
        on_boarded = request.POST.get('onboarded', False)
        if on_boarded and not (request.user.profile.on_boarded and request.user.profile.xp > 9):
            request.user.profile.increaseXP(10)
        request.user.profile.on_boarded = on_boarded == True
        request.user.profile.save()
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO,error=Message.ERROR_OCCURRED)

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
            if not action: raise Exception(ghevent)
            effective_date = parse_datetime(request.POST['effective_date'])
            if not is_aware(effective_date):
                try:
                    effective_date = make_aware(effective_date)
                except: pass
            sender = request.POST['sender']
            m_purchase = request.POST['marketplace_purchase']
            next_billing_date = parse_datetime(m_purchase['next_billing_date'])
            if not is_aware(next_billing_date):
                try:
                    next_billing_date = make_aware(next_billing_date)
                except: pass
            account = m_purchase['account']
            if account['type'] == "Organization":
                used_email = account['organization_billing_email']
            else:
                user_gh_id = account["id"]
                ghsocial = SocialAccount.objects.get(provider=GitHubProvider.id, uid=user_gh_id)
                if not ghsocial:
                    ghUser = Github.get_user_by_id(int(user_gh_id))
                    used_email = ghUser.email
                else:
                    used_email = ghsocial.extra_data['email']

            billcycle = m_purchase['billing_cycle']
            unit_count = m_purchase['unit_count']
            
            p_id = m_purchase['plan']['id']
            gh_plan = GhMarketPlan.objects.get(gh_app__gh_id=targetID,gh_id=p_id)
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
                    pre_ghsocial = SocialAccount.objects.get(provider=GitHubProvider.id, uid=pre_user_gh_id)
                    if not ghsocial:
                        pre_ghUser = Github.get_user_by_id(int(pre_user_gh_id))
                        pre_used_email = pre_ghUser.email
                    else:
                        pre_used_email = pre_ghsocial.extra_data['email']

                pre_p_id = pre_m_purchase['plan']['id']
                pre_gh_plan = GhMarketPlan.objects.get(gh_app__gh_id=targetID,gh_id=pre_p_id)
                pre_emailaddr = EmailAddress.objects.filter(email=pre_used_email).first()
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


@method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
class Robots(TemplateView):
    content_type = Code.TEXT_PLAIN
    template_name = Template.ROBOTS_TXT

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cacheKey = f"{Template.ROBOTS_TXT}_suspended_list"
        suspended = cache.get(cacheKey,[])
        if not len(suspended):
            suspended = Profile.objects.filter(
                Q(suspended=True) | Q(is_zombie=True))
            cache.set(cacheKey,suspended,settings.CACHE_SHORT)
        context = dict(**context, media=settings.MEDIA_URL,
                       suspended=suspended, ISBETA=ISBETA)
        return context


# @method_decorator(cache_page(settings.CACHE_LONG), name='dispatch')
class Manifest(TemplateView):
    content_type = Code.APPLICATION_JSON
    template_name = Template.MANIFEST_JSON

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sizes = []

        def appendWhen(path: str):
            condition = path.endswith(('icon-circle.png','icon.png'))
            if condition:
                parts = path.split('/')
                size = int(parts[len(parts)-2])
                sizes.append(size)
            return condition

        assets = getDeepFilePaths('static/graphics/self', appendWhen=appendWhen)

        assets = list(map(lambda p: str(p.replace("/static/",settings.STATIC_URL)), assets))

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

        assets = []

        def appendWhen(path: str):
            return path.endswith(('.js', '.css', '.map', '.jpg', '.webp', '.woff2', '.svg', '.png', '.jpeg')) and not (path.__contains__('/email/') or path.__contains__('/admin/'))
        assets = getDeepFilePaths(
            "static", appendWhen=appendWhen)

        def attachStaticURL(path: str):
            return str(path.replace("/static/",settings.STATIC_URL))

        assets = list(map(attachStaticURL, assets))
        assets.append(f"/{URL.OFFLINE}")
        assets.append(f"/{URL.MANIFEST}")

        cacheKey = f'localstore_{Code.SWASSETS}'
        swassets = cache.get(cacheKey, None)
        created = False
        if not swassets:
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
                swassets.value = json.dumps(assets)
                swassets.save()
                cache.set(cacheKey, swassets)
            else:
                assets = oldassets

        context = dict(**context, **renderData(dict(
            DEBUG=settings.DEBUG,
            OFFLINE=f"/{URL.OFFLINE}",
            assets=json.dumps(assets),
            noOfflineList=json.dumps([
                setPathParams(f"/{URL.ON_BOARDING}"),
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
                f"/{URL.WEBPUSH}*"
                f"/{URL.ROBOTS_TXT}",
                f"/{URL.VERSION_TXT}",
                f"/{URL.REDIRECTOR}*",
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
                setPathParams(f"/{URL.PEOPLE}{URL.People.SUCCESSORINVITE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.ZOMBIE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.BROWSE_SEARCH}*"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROJECT_TRANS_INVITE}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.LICENSE_SEARCH}*"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_FREE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_MOD}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE_CORE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.LICENSES}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.BROWSE_SEARCH}*"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.CREATE_FRAME}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.REPORT_CATEGORIES}"),
                setPathParams(
                    f"/{URL.PROJECTS}{URL.Projects.REPORT_CATEGORIES}"),
            ]),
            recacheList=json.dumps([
                f"/{URL.REDIRECTOR}*",
            ]),
            netFirstList=json.dumps([
                f"/{URL.LANDING}",
                f"/{URL.FAME_WALL}",
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_FREE}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.PROFILE_MOD}"),
                setPathParams(f"/{URL.PROJECTS}{URL.Projects.CREATE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILE}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.PROFILETAB}"),
                setPathParams(f"/{URL.PEOPLE}{URL.People.FRAMEWORK}"),
                setPathParams(f"/{URL.VIEW_SNAPSHOT}"),
                setPathParams(f"/{URL.BRANDING}"),
                setPathParams(f"/{URL.BROWSER}"),
            ])
        )))
        return context

class Strings(TemplateView):
    content_type = Code.APPLICATION_JS
    # mime_type = Code.APPLICATION_JS
    template_name = Template.STRINGS

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
            excludeUserIDs = request.user.profile.blockedIDs
            cachekey = f"{cachekey}{request.user.id}"

        limit = int(request.POST.get('limit', request.GET.get('limit', 10)))
        if type == Browse.PROJECT_SNAPSHOTS:
            if request.user.is_authenticated:
                excludeIDs = request.POST.get('excludeIDs', [])
                limit = int(request.POST.get('limit', request.GET.get('limit', 5)))
                cachekey = f"{cachekey}{limit}"
                if len(excludeIDs):
                    cachekey = cachekey + "".join(excludeIDs)
                snaps = cache.get(cachekey,[])
                snapIDs = [snap.id for snap in snaps]
                
                if not len(snaps):
                    snaps = Snapshot.objects.filter(Q(Q(base_project__admirers=request.user.profile)|Q(base_project__creator=request.user.profile)),base_project__suspended=False,base_project__trashed=False).exclude(id__in=excludeIDs).exclude(creator__user__id__in=excludeUserIDs).distinct().order_by("-created_on")[:limit]
                    snapIDs = [snap.id for snap in snaps]
                    if len(snaps):
                        cache.set(cachekey, snaps, settings.CACHE_INSTANT)
                
                data = dict(
                    html=renderString(request, Template.SNAPSHOTS, dict(snaps=snaps)),
                    snapIDs=snapIDs,
                    recommended=False
                )
                return respondJson(Code.OK, data)
            else:
                return respondJson(Code.OK,dict(snapIDs=[]))
        elif type == Browse.NEW_PROFILES:
            profiles = cache.get(cachekey,[])
            if not len(profiles):
                if request.user.is_authenticated:
                    excludeUserIDs.append(request.user.profile.getUserID())
                profiles = Profile.objects.exclude(user__id__in=excludeUserIDs).filter(
                    user__emailaddress__verified=True,
                    createdOn__gte=(timezone.now()+timedelta(days=-15)),
                    suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[:limit]
                if len(profiles) < 5:
                    profiles = Profile.objects.exclude(user__id__in=excludeUserIDs).filter(
                        user__emailaddress__verified=True,
                        createdOn__gte=(
                            timezone.now()+timedelta(days=-30)),
                        suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[:limit]
                if len(profiles) < 10:
                    profiles = Profile.objects.exclude(user__id__in=excludeUserIDs).filter(
                        user__emailaddress__verified=True,
                        createdOn__gte=(
                            timezone.now()+timedelta(days=-60)),
                        suspended=False, to_be_zombie=False, is_active=True).order_by('-createdOn')[:limit]
                if len(profiles):
                    cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_NEWBIE, dict(profiles=profiles, count=len(profiles)))

        elif type == Browse.NEW_PROJECTS:
            projects = cache.get(cachekey,[])
            if not len(projects):
                projects = BaseProject.objects.filter(createdOn__gte=(
                    timezone.now()+timedelta(days=-30)), suspended=False, trashed=False).exclude(creator__user__id__in=excludeUserIDs).order_by('-createdOn')[:limit]

                projects = list(set(list(filter(lambda p: p.is_approved, projects))))
                if len(projects):
                    cache.set(cachekey, projects, settings.CACHE_MINI)

            return projectsRendererstr(request, Template.Projects.BROWSE_NEWBIE, dict(projects=projects, count=len(projects)))

        elif type == Browse.RECENT_WINNERS:
            results = cache.get(cachekey, [])
            if not len(results):
                results = Result.objects.filter(competition__resultDeclared=True, competition__startAt__gte=(
                    timezone.now()+timedelta(days=-6))).order_by('-competition__endAt')[:limit]
                if len(results):
                    cache.set(cachekey, results, settings.CACHE_MINI)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_RECENT_WINNERS, dict(results=results, count=len(results))))

        elif type == Browse.RECOMMENDED_PROJECTS:
            projects = cache.get(cachekey,[])
            if not len(projects):
                query = Q()
                authquery = query
                if request.user.is_authenticated:
                    query = Q(topics__in=request.user.profile.getTopics())
                    authquery = ~Q(creator=request.user.profile)
                
                projects = BaseProject.objects.filter(Q(trashed=False,suspended=False),authquery, query).exclude(creator__user__id__in=excludeUserIDs)[:limit]
                projects = list(set(list(filter(lambda p: p.is_approved,projects))))
                
                if len(projects) < 3:
                    projects = BaseProject.objects.filter(Q(trashed=False,suspended=False),authquery).exclude(creator__user__id__in=excludeUserIDs)[:limit]
                    projects = list(set(list(filter(lambda p: p.is_approved,projects))))
                if len(projects):
                    cache.set(cachekey, projects, settings.CACHE_MINI)
            
            return projectsRendererstr(request, Template.Projects.BROWSE_RECOMMENDED, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_TOPICS:
            # TODO
            return HttpResponseBadRequest(Browse.TRENDING_TOPICS)
        elif type == Browse.TRENDING_PROJECTS:
            projects = cache.get(cachekey,[])
            if not len(projects):
                query = Q()
                authquery = query
                if request.user.is_authenticated:
                    query = Q(topics__in=request.user.profile.getTopics())
                    authquery = ~Q(creator=request.user.profile)

                projects = BaseProject.objects.filter(Q(trashed=False,suspended=False),authquery, query).exclude(creator__user__id__in=excludeUserIDs)[:limit]
                projects = list(set(list(filter(lambda p: p.is_approved,projects))))

                if len(projects) < 3:
                    projects = BaseProject.objects.filter(Q(trashed=False,suspended=False),authquery).exclude(creator__user__id__in=excludeUserIDs)[:limit]
                    projects = list(set(list(filter(lambda p: p.is_approved,projects))))
                if len(projects):
                    cache.set(cachekey, projects, settings.CACHE_MINI)
    
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_PROFILES:
            # TODO
            return HttpResponseBadRequest(type)
        elif type == Browse.NEWLY_MODERATED:
            # TODO
            return HttpResponseBadRequest(type)
        elif type == Browse.HIGHEST_MONTH_XP_PROFILES:
            # TODO
            return HttpResponseBadRequest(type)
        elif type == Browse.LATEST_COMPETITIONS:
            competitions = cache.get(cachekey,[])
            if not len(competitions):
                competitions=Competition.objects.filter(hidden=False,is_draft=False).order_by("-startAt")[:limit]
                if len(competitions):
                    cache.set(cachekey,competitions,settings.CACHE_MINI)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_LATEST_COMP, dict(competitions=competitions, count=len(competitions))))
        elif type == Browse.TRENDING_MENTORS:
            mentors = cache.get(cachekey,[])
            if not len(mentors):
                mentors = Profile.objects.filter(is_mentor=True,suspended=False,is_active=True,to_be_zombie=False).order_by("-xp")[:limit]
                if request.user.is_authenticated:
                    mentors = request.user.profile.filterBlockedProfiles(mentors)
                if len(mentors):
                    cache.set(cachekey, mentors, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING_MENTORS, dict(mentors=mentors, count=len(mentors)))
        elif type == Browse.TRENDING_MODERATORS:
            moderators = cache.get(cachekey,[])
            if not len(moderators):
                moderators = Profile.objects.filter(is_moderator=True,suspended=False,is_active=True,to_be_zombie=False).order_by("-xp")[:limit]
                if request.user.is_authenticated:
                    moderators = request.user.profile.filterBlockedProfiles(moderators)
                if len(moderators):
                    cache.set(cachekey, moderators, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING_MODS, dict(moderators=moderators, count=len(moderators)))
        elif type == Browse.DISPLAY_MENTORS:
            dmentors = cache.get(cachekey,[])
            if not len(dmentors):
                dmentors = DisplayMentor.objects.filter(hidden=False).order_by("-createdOn")
                if len(dmentors):
                    cache.set(cachekey, dmentors, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_DISPLAY_MENTORS, dict(dmentors=dmentors, count=len(dmentors)))
        else:
            return HttpResponseBadRequest(type)
    except Exception as e:
        errorLog(e)
        if request.POST.get(Code.JSON_BODY, False):
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)
