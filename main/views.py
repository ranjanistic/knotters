from datetime import timedelta
from json import dumps as jsondumps
from json import loads as jsonloads
from os import path as ospath
from uuid import UUID
from people.views import browseSearch as peopleSearch
from projects.views import browseSearch as projectsSearch
from compete.views import browseSearch as competeSearch
from howto.views import browseSearch as howtoSearch
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from compete.methods import competitionProfileData
from compete.methods import rendererstr as competeRendererstr
from compete.models import Competition, Result, Submission
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Count, Q
from django.http.response import (Http404, HttpResponse,
                                  HttpResponseBadRequest, JsonResponse)
from django.shortcuts import redirect, render
from django.template.exceptions import TemplateDoesNotExist
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.utils.timezone import is_aware, make_aware
from django.views.decorators.cache import cache_control, cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView
from management.methods import competitionManagementRenderData, labelRenderData
from management.models import (GhMarketApp, GhMarketPlan, HookRecord,
                               ThirdPartyLicense)
from moderation.methods import moderationRenderData
from moderation.models import LocalStorage
from people.methods import profileRenderData
from people.methods import rendererstr as peopleRendererstr
from howto.methods import rendererstr as howtoRendererstr
from howto.models import Article
from people.models import (CoreMember, DisplayMentor, CoreContributor, GHMarketPurchase,
                           Profile, Topic)
from projects.methods import coreProfileData, freeProfileData
from projects.methods import rendererstr as projectsRendererstr
from projects.methods import verifiedProfileData, baseProfileData
from projects.models import (BaseProject, CoreProject, FreeProject, LegalDoc,
                             Project, Snapshot)
from ratelimit.decorators import ratelimit
from rjsmin import jsmin

from .bots import Github
from .decorators import (decode_JSON, dev_only, github_only,
                         normal_profile_required, require_JSON)
from .env import ADMINPATH, ISBETA, ISPRODUCTION
from .mailers import featureRelease
from .methods import (errorLog, getDeepFilePaths, renderData, renderString,
                      renderView, respondJson, respondRedirect, verify_captcha)
from .strings import (COMPETE, DOCS, MANAGEMENT, MODERATION, PEOPLE, PROJECTS, HOWTO,
                      URL, Browse, Code, Event, Message, Template,
                      setPathParams, setURLAlerts)
from howto.methods import articleRenderData


@require_GET
def offline(request: WSGIRequest) -> HttpResponse:
    """To render offline view (particularly stored in client cache)

    Methods: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderView(request, Template.OFFLINE)


@require_GET
def branding(request: WSGIRequest) -> HttpResponse:
    """To render branding page

    Methods: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderView(request, Template.BRANDING)


@dev_only
@require_GET
def mailtemplate(request: WSGIRequest, template: str) -> HttpResponse:
    """To render an email template. Only used in development.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.
        template (str): The template name without extension.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderView(request, f'account/email/{template}')


@require_GET
@dev_only
def template(request: WSGIRequest, template: str) -> HttpResponse:
    """To render a template. Only used in development.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.
        template (str): The template name without extension.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderView(request, template)


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    """To render the index page (home/root page)

    Methods: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: If user is logged in, but not on-boarded, redirect to onboarding.
        HttpResponse: The rendered text/html view with context.
            If logged in, renders dashboard (home.html), else renders index.html

    NOTE: The template index.html is used for both logged in and logged out users. (the about page)

        The template home.html is only used for logged in users (the feed/dashboard).

        But main.views.index & main.views.home render these two interchangably, i.e.,

            main.views.home -> main.view.index (301) if logged in, else index.html

            main.views.index -> home.html if logged in, else index.html

    """

    competition: Competition = Competition.latest_competition()
    if request.user.is_authenticated:
        if not request.user.profile.on_boarded:
            return respondRedirect(path=URL.ON_BOARDING)
        return renderView(request, Template.HOME, dict(competition=competition))

    topics = Topic.homepage_topics()
    project = BaseProject.homepage_project()
    return renderView(request, Template.INDEX, dict(topics=topics, project=project, competition=competition))


@require_GET
def home(request: WSGIRequest) -> HttpResponse:
    """To render the home page (the about page) (index.html)

    Methods: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: If user is not logged in, redirect to root path (main.views.index)
        HttpResponse: The rendered text/html view of index.html.
    """
    if not request.user.is_authenticated:
        return redirect(URL.ROOT)
    competition: Competition = Competition.latest_competition()
    topics = Topic.homepage_topics()
    project: BaseProject = BaseProject.homepage_project()
    return renderView(request, Template.INDEX, dict(topics=topics, project=project, competition=competition))


@require_GET
def homeDomains(request: WSGIRequest, domain: str) -> HttpResponse:
    """To respond with homepage domains tab section text/html content.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.
        domain (str): The domain (section) name.

    Returns:
        HttpResponse: The rendered text/html component content.
    """
    return renderView(request, domain, fromApp="home")


@require_GET
def search_view(request: WSGIRequest) -> HttpResponse:
    """To render the search view

    Methods: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view with context.
    """
    try:
        return renderView(request, Template.SEARCH)
    except Exception as e:
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='2/s', block=True)
@decode_JSON
def search_results(request: WSGIRequest) -> HttpResponse:
    """To respond with search results.

    Methods: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view with context.
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ""))[
            :100].strip()

        if not query:
            raise KeyError(query)
        response1 = peopleSearch(request)
        people = response1.content.decode(Code.UTF_8)
        response2 = projectsSearch(request)
        projects = response2.content.decode(Code.UTF_8)
        response3 = competeSearch(request)
        compete = response3.content.decode(Code.UTF_8)
        response4 = howtoSearch(request)
        howto = response4.content.decode(Code.UTF_8)
        return respondJson(Code.OK, dict(people=people, projects=projects, compete=compete, howto=howto))
    except (KeyError, ValidationError) as e:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        return redirect(setURLAlerts(f"/{URL.SEARCH}", error=Message.INVALID_REQUEST))
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        return redirect(setURLAlerts(f"/{URL.SEARCH}", error=Message.ERROR_OCCURRED))


@require_GET
def redirector(request: WSGIRequest) -> HttpResponse:
    """To redirect to any path provided by the query string.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.
        request.GET.n (str): The path to redirect to.

    Returns:
        HttpResponse: renders the texthtml forwarding view if path is not a part of the app.
        HttpResponseRedirect: The redirect response to the path provided, if path is safe, or to root path if any exception occurs.

    NOTE: This redirector is primarily meant for client side service worker to clear cache,
        whenever this redirector path is requested. For example: after logout, to clear
        user specific cached data for the expired session, redirector path can be used to forward
        to after logout page, to let the client service worker know that all user specific cache should be cleared now.
    """
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
def at_nickname(request: WSGIRequest, nickname: str) -> HttpResponse:
    """To redirect to profile url of the user with the nickname provided.
    Primarily used for the short links of user profile.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.
        nickname (str): The nickname of the user.

    Raises:
        Http404: If user with the nickname provided does not exist, or any exception occurs.

    Returns:
        HttpResponseRedirect: The redirect response to the profile url of the user with the nickname provided.

    NOTE: nickanme == "me" is reserved for the logged in user only, thus it is not allowed to be used as a nickname for any profile.
    """
    try:
        if nickname == "me":
            if not request.user.is_authenticated:
                return redirect(URL.Auth.LOGIN)
            return redirect(request.user.profile.get_link)
        if request.user.is_authenticated:
            if nickname == request.user.profile.get_nickname():
                return redirect(request.user.profile.get_link)
        profile_url: str = Profile.nickname_profile_url(nickname)
        return redirect(profile_url)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def at_emoji(request: WSGIRequest, emoticon: str) -> HttpResponse:
    """!EXPERIMENTAL!
    To redirect to profile url of the user with the emoticon provided.
    Primarily used for the short emoticon links of user profile.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.
        emoticon (str): The emoticon of the user.

    Raises:
        Http404: If user with the emoticon provided does not exist, or any exception occurs.

    Returns:
        HttpResponseRedirect: The redirect response to the profile url of the user with the emoticon provided.
    """
    try:
        if request.user.is_authenticated:
            if emoticon == request.user.profile.emoticon:
                return redirect(request.user.profile.get_link)
        profile_url = Profile.emoticon_profile_url(emoticon)
        return redirect(profile_url)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_GET
def on_boarding(request: WSGIRequest) -> HttpResponse:
    """To render the on boarding view for the logged in user.

    Methods: GET

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If any exception occurs.

    Returns:
        HttpResponse: The rendered text/html view of on_boarding.html.
    """
    try:
        return renderView(request, Template.ON_BOARDING)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def on_boarding_update(request: WSGIRequest) -> JsonResponse:
    """To update on boarding status of the logged in user.

    Methods: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: The response json with main.strings.Code.OK if the on boarding status is updated successfully,
            else main.strings.Code.NO
    """
    try:
        on_boarded = request.POST.get('onboarded', False)
        if on_boarded and not (request.user.profile.on_boarded and request.user.profile.xp > 9):
            request.user.profile.increaseXP(10, reason="On boarding complete")
        request.user.profile.on_boarded = on_boarded == True
        request.user.profile.save()
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_GET
def docIndex(request: WSGIRequest) -> HttpResponse:
    """To render docs & statements homepage

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view of hompage of docs & statements
    """
    return renderView(request, Template.Docs.INDEX, fromApp=DOCS, data=dict(docs=LegalDoc.get_all()))


@require_GET
def docs(request: WSGIRequest, type: str) -> HttpResponse:
    """To render individual legal doc/guidleine page

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        type (str): The type of the doc/guideline (pseudonym or docs/template name)

    Raises:
        Http404: If the doc/guideline is not found

    Returns:
        HttpResponse: The rendered text/html view of the doc/guideline with content
    """
    try:
        doc = LegalDoc.get_doc(pseudonym=type)
        return renderView(request, Template.Docs.DOC, fromApp=DOCS, data=dict(doc=doc))
    except ObjectDoesNotExist:
        pass
    except Exception as e:
        errorLog(e)
        raise Http404(e)
    try:
        return renderView(request, type, fromApp=DOCS, data=dict(tpls=ThirdPartyLicense.get_all()))
    except TemplateDoesNotExist:
        raise Http404(type)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def landing(request: WSGIRequest) -> HttpResponse:
    """To render the traditional landing page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view of the landing page.
    """
    return renderView(request, Template.LANDING, dict(
        gh_market_app=GhMarketApp.get_all().first()
    ))


@require_GET
def applanding(request: WSGIRequest, subapp: str) -> HttpResponse:
    """DEPRECATED"""
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
def fameWall(request: WSGIRequest) -> HttpResponse:
    """To render the wall of fame

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view of wall of fame.
    """
    return renderView(request, Template.FAME_WALL)


@require_JSON
def verifyCaptcha(request: WSGIRequest) -> JsonResponse:
    """To verify google recaptcha response

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: The response json with main.strings.Code.OK if the captcha is verified successfully,
            else main.strings.Code.NO
    """
    try:
        capt_response = request.POST['g-recaptcha-response']
        if verify_captcha(capt_response):
            return respondJson(Code.OK)
        return respondJson(Code.NO if ISPRODUCTION else Code.OK)
    except KeyError:
        return respondJson(Code.NO if ISPRODUCTION else Code.OK, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO if ISPRODUCTION else Code.OK, error=Message.ERROR_OCCURRED)


@require_GET
def snapshot(request: WSGIRequest, snapID: UUID) -> HttpResponse:
    """To render the snapshot view of the given snapID (standalone snapshot)

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        snapID (str): The snapshot ID

    Raises:
        Http404: If the snapshot is not found, or exception occurs

    Returns:
        HttpResponse: The rendered text/html standalone view of the snapshot.
    """
    try:
        snapshot = Snapshot.objects.get(id=snapID)
        return renderView(request, Template.VIEW_SNAPSHOT, dict(snapshot=snapshot))
    except ObjectDoesNotExist as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@decode_JSON
def donation(request: WSGIRequest) -> HttpResponse:
    """To render the donation page and handle all donation requests.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view of donation page.
        JsonResponse: the response json with main.strings.Code.OK if request succeeds, else main.strings.Code.NO.

    """
    if request.method == "POST":
        return respondJson(Code.NO)
    else:
        return renderView(request, Template.DONATION)


@require_GET
def thankyou(request: WSGIRequest) -> HttpResponse:
    """To render the donation page and handle all donation requests.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view of donation page.
        JsonResponse: the response json with main.strings.Code.OK if request succeeds, else main.strings.Code.NO.

    """
    cachekey = f"thankyou_{type}{request.LANGUAGE_CODE}"
    contributors = cache.get(cachekey, [])
    count = len(contributors)
    if not count:
        contributors = CoreContributor.objects.filter(
            hidden=False).order_by("createdOn")
        count = len(contributors)
    if count:
        cache.set(cachekey, contributors, settings.CACHE_INSTANT)
    return renderView(request, Template.THANKYOU, dict(contributors=contributors))


@require_GET
@cache_control(no_cache=True, public=True, max_age=settings.CACHE_MINI)
def scripts(request: WSGIRequest, script: str) -> HttpResponse:
    """To render the global dynamic script files depending on the script param

    Args:
        request (WSGIRequest): The request object.
        script (str): The script file name

    Raises:
        Http404: If the script is not found

    Returns:
        HttpResponse: The rendered text/javascript view of the script file.
    """
    if script not in Template.script.getScriptTemplates():
        raise Http404("Script not found")
    stringrender = render_to_string(script, request=request, context=renderData(
        fromApp=request.GET.get('fromApp', '')))
    if not settings.DEBUG:
        stringrender = jsmin(stringrender)
    return HttpResponse(stringrender, content_type=Code.APPLICATION_JS)


@require_GET
@cache_control(no_cache=True, public=True, max_age=settings.CACHE_MINI)
def scripts_subapp(request: WSGIRequest, subapp: str, script: str) -> HttpResponse:
    """To render the application specific dynamic script files depending on the subapp & script param.
    The scripts are rendered with the page specific context as well, determined by script name.
    Some scripts need extra query data depending upon the specificity of the page in which they are loaded,
    For ex. User profile specific page's scripts may require userID for proper context.

    Args:
        request (WSGIRequest): The request object.
        subapp (str): The subapplication module name under which the script file is located
        script (str): The script file name

    Raises:
        Http404: If the script is not found

    Returns:
        HttpResponse: The rendered text/javascript view of the script file.
    """
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
        elif script == Template.Script.PROFILE:
            data = baseProfileData(request, projectID=projectID)
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
    elif subapp == HOWTO:
        nickname = request.GET.get('nickname', "")
        if script == Template.Script.ARTICLE or script == Template.Script.ARTICLE_EDIT:
            data = articleRenderData(request, nickname)

    stringrender = render_to_string(f"{subapp}/scripts/{script}", request=request,
                                    context=renderData(fromApp=request.GET.get('fromApp', subapp), data=data))
    if not settings.DEBUG:
        stringrender = jsmin(stringrender)
    return HttpResponse(stringrender, content_type=Code.APPLICATION_JS)


def handler403(request: WSGIRequest, exception: Exception, template_name="403.html") -> HttpResponse:
    """To render the 403 error page (custom made)
    """
    response = render(template_name)
    response.status_code = 403
    return response


@csrf_exempt
@github_only
def githubEventsListener(request: WSGIRequest, type: str, targetID: str) -> HttpResponse:
    """To handle the github webhook requests.

    NOTE: This is not the handler for project respository webhooks. Check that in projects.views

    TODO: Make the webhook handler logic a queue based task, see projects.views.githubEventsListener for this.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.
        type (str): The type of the webhook event
        targetID (str): The target ID of the webhook event

    Raises:
        Http404: If an exception occurs

    Returns:
        HttpResponse: main.strings.Code.OK if request succeeds, else main.strings.Code.NO.
    """
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
                    featureRelease(release['name'], release['body'])

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
        raise Http404(e)


class Robots(TemplateView):
    """To render the robots.txt

    METHODS: GET
    """
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
    """To render the sitemap

    METHODS: GET
    """
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


class Manifest(TemplateView):
    """To render the webapp manifest

    METHODS: GET
    """
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
    """To render the service worker

    METHODS: GET
    """
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
                f"/{URL.SEARCH_RESULT}",
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
                setPathParams(f"/{URL.HOWTO}{URL.INDEX}"),
                setPathParams(f"/{URL.HOWTO}{URL.Howto.CREATE}"),
                setPathParams(f"/{URL.HOWTO}{URL.Howto.EDIT}"),
                setPathParams(f"/{URL.HOWTO}{URL.Howto.VIEW}"),
                setPathParams(f"/{URL.HOWTO}{URL.Howto.ADMIRATIONS}"),
                setPathParams(f"/{URL.HOWTO}{URL.Howto.BROWSE_SEARCH}"),
                setPathParams(f"/{URL.VIEW_SNAPSHOT}"),
                setPathParams(f"/{URL.BRANDING}"),
                setPathParams(f"/{URL.BROWSER}"),
                setPathParams(f"/{URL.SCRIPTS}"),
                setPathParams(f"/{URL.SCRIPTS_SUBAPP}"),
                setPathParams(f"/{URL.THANKYOU}"),
            ])
        )))
        return context


class Version(TemplateView):
    """To render the version.txt

    METHODS: GET
    """
    content_type = Code.TEXT_PLAIN
    template_name = Template.VERSION

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@decode_JSON
def browser(request: WSGIRequest, type: str) -> HttpResponse:
    """To respond with browsable text/html content (component),
        mainly for personal feed/home of logged in users.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object
        type (str): type of browsable content to render (an attribute of main.strings.Browse)

    Raises:
        Http404: If any exception occurs

    Returns:
        HttpResponseBadRequest: If the browsable content type is not valid
        HttpResponse: The response text/html component content.
        JsonResponse: The response json content with main.strings.Code.OK and requested content
    """
    try:
        r = settings.REDIS_CLIENT
        cachekey = f"main_browser_{type}{request.LANGUAGE_CODE}"
        excludeUserIDs = []
        if request.user.is_authenticated:
            excludeUserIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}{request.user.id}"

        limit = int(request.POST.get('limit', request.GET.get('limit', 10)))
        if type == Browse.PROJECT_SNAPSHOTS:
            if request.user.is_authenticated:
                start = request.POST.get('start', 0)
                limit = int(request.POST.get(
                    'limit', request.GET.get('limit', 5)))
                cachekey = f"{cachekey}{limit}_{start}"
                snaps = cache.get(cachekey, [])
                snapIDs = [snap.id for snap in snaps]
                if not len(snaps):
                    snap_ids = r.lrange(f"{Browse.PROJECT_SNAPSHOTS}_{request.user.profile.id}", start, start+limit-1)
                    queryset = Snapshot.objects.filter(id__in=snap_ids)
                    snaps = sorted(queryset, key=lambda x : snap_ids.index(str(x.id)))
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
                profile_ids = r.lrange(Browse.NEW_PROFILES, 0, -1)
                queryset = Profile.objects.filter(id__in=profile_ids).exclude(
                    user__id__in=excludeUserIDs)[:limit]
                profiles = sorted(queryset, key=lambda x: profile_ids.index(str(x.id)))
                cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_NEWBIE, dict(profiles=profiles, count=len(profiles)))

        elif type == Browse.NEW_PROJECTS:
            projects = cache.get(cachekey, [])
            if not len(projects):
                project_ids = r.lrange(Browse.NEW_PROJECTS, 0, -1)
                queryset = BaseProject.objects.filter(id__in=project_ids).exclude(
                    creator__user__id__in=excludeUserIDs).distinct()[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                cache.set(cachekey, projects, settings.CACHE_MINI)

            return projectsRendererstr(request, Template.Projects.BROWSE_NEWBIE, dict(projects=projects, count=len(projects)))

        elif type == Browse.RECENT_WINNERS:
            results = cache.get(cachekey, None)
            if results is None:
                result_ids = r.lrange(Browse.RECENT_WINNERS, 0, -1)
                queryset = Result.objects.filter(id__in=result_ids)[:limit]
                results = sorted(queryset, key=lambda x: result_ids.index(str(x.id)))
                cache.set(cachekey, results, settings.CACHE_MINI)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_RECENT_WINNERS, dict(results=results, count=len(results))))

        elif type == Browse.RECOMMENDED_PROJECTS:
            projects = cache.get(cachekey, [])
            count = len(projects)
            if not count:
                if request.user.is_authenticated:
                    project_ids = r.lrange(f"{Browse.RECOMMENDED_PROJECTS}_{request.user.profile.id}", 0, -1)
                else:
                    project_ids = r.lrange(Browse.RECOMMENDED_PROJECTS)
                queryset = BaseProject.objects.filter(id__in=project_ids).distinct()[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                count = len(projects)

                if count:
                    cache.set(cachekey, projects, settings.CACHE_MINI)

            return projectsRendererstr(request, Template.Projects.BROWSE_RECOMMENDED, dict(projects=projects, count=count))
        elif type == Browse.TRENDING_TOPICS:
            # TODO
            # topics = Topic.objects.filter()[:10]
            # return peopleRendererstr(request, Template.People.BROWSE_TRENDING_TOPICS, dict(topics=topics, count=len(topics)))
            pass
        elif type == Browse.TRENDING_PROJECTS:
            projects = cache.get(cachekey, [])
            if not len(projects):
                project_ids = r.lrange(Browse.TRENDING_PROJECTS, 0, -1)
                queryset = BaseProject.objects.filter(id__in=project_ids).exclude(
                    creator__user__id__in=excludeUserIDs).distinct()[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_PROFILES:
            profiles = cache.get(cachekey, [])
            if not len(profiles):
                profile_ids = r.lrange(Browse.TRENDING_PROFILES, 0, -1)
                queryset = Profile.objects.filter(id__in=profile_ids).exclude(
                    user__id__in=excludeUserIDs)[:limit]
                profiles = sorted(queryset, key=lambda x: profile_ids.index(str(x.id)))
                cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING, dict(profiles=profiles, count=len(profiles)))
        elif type == Browse.NEWLY_MODERATED:
            projects = cache.get(cachekey, [])
            if not len(projects):
                project_ids = r.lrange(Browse.NEWLY_MODERATED, 0, -1)
                queryset = BaseProject.objects.filter(id__in=project_ids).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_NEWLY_MODERATED, dict(projects=projects, count=len(projects)))
        elif type == Browse.HIGHEST_MONTH_XP_PROFILES:
            profiles = cache.get(cachekey, [])
            if not len(profiles):
                profile_ids = r.lrange(Browse.HIGHEST_MONTH_XP_PROFILES, 0, -1)
                queryset = Profile.objects.filter(id__in=profile_ids).exclude(
                    user__id__in=excludeUserIDs)[:limit]
                profiles = sorted(queryset, key=lambda x: profile_ids.index(str(x.id)))
                cache.set(cachekey, profiles, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_HIGHEST_MONTH_XP_PROFILES, dict(profiles=profiles, count=len(profiles)))
        elif type == Browse.LATEST_COMPETITIONS:
            competitions = cache.get(cachekey, [])
            if not len(competitions):
                competition_ids = r.lrange(Browse.LATEST_COMPETITIONS, 0, -1)
                queryset = Competition.objects.filter(id__in=competition_ids)[:limit]
                competitions = sorted(queryset, key=lambda x: competition_ids.index(str(x.id)))
                cache.set(cachekey, competitions, settings.CACHE_MINI)
            return HttpResponse(competeRendererstr(request, Template.Compete.BROWSE_LATEST_COMP, dict(competitions=competitions, count=len(competitions))))
        elif type == Browse.TRENDING_MENTORS:
            mentors = cache.get(cachekey, [])
            if not len(mentors):
                profile_ids = r.lrange(Browse.TRENDING_MENTORS, 0, -1)
                queryset = Profile.objects.filter(id__in=profile_ids)[:limit]
                mentors = sorted(queryset, key=lambda x: profile_ids.index(str(x.id)))
                if request.user.is_authenticated:
                    mentors = request.user.profile.filterBlockedProfiles(
                        mentors)
                cache.set(cachekey, mentors, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING_MENTORS, dict(mentors=mentors, count=len(mentors)))
        elif type == Browse.TRENDING_MODERATORS:
            moderators = cache.get(cachekey, [])
            if not len(moderators):
                profile_ids = r.lrange(Browse.TRENDING_MODERATORS, 0, -1)
                queryset = Profile.objects.filter(id__in=profile_ids)[:limit]
                moderators = sorted(queryset, key=lambda x: profile_ids.index(str(x.id)))
                if request.user.is_authenticated:
                    moderators = request.user.profile.filterBlockedProfiles(
                        moderators)
                cache.set(cachekey, moderators, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_TRENDING_MODS, dict(moderators=moderators, count=len(moderators)))
        elif type == Browse.DISPLAY_MENTORS:
            dmentors = cache.get(cachekey, [])
            count = len(dmentors)
            if not count:
                dmentor_ids = r.lrange(Browse.DISPLAY_MENTORS, 0, -1)
                queryset = DisplayMentor.objects.filter(id__in=dmentor_ids)[:limit]
                dmentors = sorted(queryset, key=lambda x: dmentor_ids.index(str(x.id)))
                count = len(dmentors)
                if count:
                    cache.set(cachekey, dmentors, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_DISPLAY_MENTORS, dict(dmentors=dmentors, count=count))
        elif type == Browse.CORE_MEMBERS:
            coremems = cache.get(cachekey, [])
            count = len(coremems)
            if not count:
                coremem_ids = r.lrange(Browse.CORE_MEMBERS, 0, -1)
                queryset = CoreMember.objects.filter(id__in=coremem_ids)[:limit]
                coremems = sorted(queryset, key=lambda x: coremem_ids.index(str(x.id)))
                count = len(coremems)
                if count:
                    cache.set(cachekey, coremems, settings.CACHE_MINI)
            return peopleRendererstr(request, Template.People.BROWSE_CORE_MEMBERS, dict(coremems=coremems, count=count))
        elif type == Browse.TOPIC_PROJECTS:
            if request.user.is_authenticated:
                projects = cache.get(cachekey, [])
                topic = r.get(f"{Browse.TOPIC_PROJECTS}_{request.user.profile.id}_topic")
                if not projects:
                    project_ids = r.lrange(Browse.TOPIC_PROJECTS, 0, -1)
                    queryset = BaseProject.objects.filter(id__in=project_ids).distinct()[:limit]
                    projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                    cache.set(cachekey, projects, settings.CACHE_MINI)
                return projectsRendererstr(request, Template.Projects.BROWSE_TOPIC_PROJECTS, dict(projects=projects, count=len(projects), topic=topic))
            else:
                pass
        elif type == Browse.TOPIC_PROFILES:
            if request.user.is_authenticated:
                profiles = cache.get(cachekey, [])
                topic = r.get(f"{Browse.TOPIC_PROFILES}_{request.user.profile.id}_topic")
                if not profiles:
                    profile_ids = r.lrange(f"{Browse.TOPIC_PROFILES}_{request.user.profile.id}", 0, -1)
                    queryset = Profile.objects.filter(id__in=profile_ids)[:limit]
                    profiles = sorted(queryset, key=lambda x: profile_ids.index(str(x.id)))
                    cache.set(cachekey, profiles, settings.CACHE_MINI)
                return peopleRendererstr(request, Template.People.BROWSE_TOPIC_PROFILES, dict(profiles=profiles, count=len(profiles), topic=topic))
            else:
                pass
        elif type == Browse.TRENDING_CORE:
            projects = cache.get(cachekey, [])
            if not len(projects):
                project_ids = r.lrange(Browse.TRENDING_CORE, 0, -1)
                queryset = CoreProject.objects.filter(id__in=project_ids).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING_CORE, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_VERIFIED:
            projects = cache.get(cachekey, [])
            if not len(projects):
                project_ids = r.lrange(Browse.TRENDING_VERIFIED, 0, -1)
                queryset = Project.objects.filter(id__in=project_ids).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING_VERIFIED, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_QUICK:
            projects = cache.get(cachekey, [])
            if not len(projects):
                project_ids = r.lrange(Browse.TRENDING_QUICK, 0, -1)
                queryset = FreeProject.objects.filter(id__in=project_ids).exclude(
                    creator__user__id__in=excludeUserIDs)[:limit]
                projects = sorted(queryset, key=lambda x: project_ids.index(str(x.id)))
                cache.set(cachekey, projects, settings.CACHE_MINI)
            return projectsRendererstr(request, Template.Projects.BROWSE_TRENDING_QUICK, dict(projects=projects, count=len(projects)))
        elif type == Browse.TRENDING_ARTICLES:
            articles = cache.get(cachekey, [])
            if not len(articles):
                article_ids = r.lrange(Browse.TRENDING_ARTICLES, 0, -1)
                queryset = Article.objects.filter(id__in=article_ids).exclude(
                    author__user__id__in=excludeUserIDs)[:limit]
                articles = sorted(queryset, key=lambda x: article_ids.index(str(x.id)))
                cache.set(cachekey, articles, settings.CACHE_MINI)
            return howtoRendererstr(request, Template.Howto.BROWSE_TRENDING_ARTICLES, dict(articles=articles, count=len(articles)))
        else:
            return HttpResponseBadRequest(type)
        return HttpResponse()
    except Exception as e:
        errorLog(e)
        if request.POST.get(Code.JSON_BODY, False):
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)