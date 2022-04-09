from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import validate_email
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.http.response import (Http404, HttpResponse,
                                  HttpResponseBadRequest, HttpResponseRedirect)
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from main.decorators import (decode_JSON, github_bot_only, github_only,
                             manager_only, moderator_only,
                             normal_profile_required, require_JSON)
from main.env import PUBNAME
from main.exceptions import InvalidUserOrProfile
from main.methods import (addMethodToAsyncQueue, base64ToFile,
                          base64ToImageFile, errorLog, renderString,
                          respondJson, respondRedirect)
from main.strings import URL, Action, Code, Message, Template, setURLAlerts
from management.models import GhMarketApp, ReportCategory
from moderation.methods import (assignModeratorToObject,
                                requestModerationForCoreProject,
                                requestModerationForObject)
from people.methods import addTopicToDatabase
from people.models import Profile, Topic
from ratelimit.decorators import ratelimit

from .apps import APPNAME
from .mailers import *
from .methods import (addTagToDatabase, coreProfileData,
                      createConversionProjectFromCore,
                      createConversionProjectFromFree, createCoreProject,
                      createFreeProject, createProject,
                      deleteGhOrgCoreepository, deleteGhOrgVerifiedRepository,
                      freeProfileData, getProjectLiveData,
                      handleGithubKnottersRepoHook, renderer, renderer_stronly,
                      rendererstr, uniqueRepoName, verifiedProfileData)
from .models import (AppRepository, Asset, BaseProject,
                     BaseProjectCoCreatorInvitation, BotHookRecord, Category,
                     CoreModerationTransferInvitation, CoreProject,
                     CoreProjectDeletionRequest, CoreProjectHookRecord,
                     CoreProjectVerificationRequest, FreeProject,
                     FreeProjectVerificationRequest, FreeRepository, License,
                     Project, ProjectHookRecord,
                     ProjectModerationTransferInvitation, ProjectSocial,
                     ProjectTag, ProjectTopic, ProjectTransferInvitation,
                     Snapshot, Tag, VerProjectDeletionRequest)
from .receivers import *


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    """To render projects home page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderer(request, Template.Projects.INDEX)


@require_GET
def allLicences(request: WSGIRequest) -> HttpResponse:
    """To render all public licences view.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If any exception occurs.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    try:
        public = License.objects.filter(public=True)
        owned = []
        if request.user.is_authenticated:
            owned = License.objects.filter(creator=request.user.profile)
            public = public.exclude(creator=request.user.profile)
        return renderer(request, Template.Projects.LICENSE_INDEX, dict(licenses=public, custom=owned))
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@decode_JSON
def public_licenses(request: WSGIRequest) -> JsonResponse:
    """To respond with list of public licenses.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.
        request.POST.content/request.GET.content (bool): Whether to return the content of the licenses as well.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and list of licenses, or main.strings.Code.NO
    """

    try:
        content = request.POST.get('content', request.GET.get("content", None))
        licenses = License.get_all()
        publices = []
        for l in licenses:
            if content:
                publices.append(dict(id=l.id, name=l.name, keyword=l.keyword,
                                description=l.description, content=l.content))
            else:
                publices.append(dict(id=l.id, name=l.name,
                                keyword=l.keyword, description=l.description,))
        return respondJson(Code.OK, dict(licenses=publices))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_GET
def licence(request: WSGIRequest, id: UUID) -> HttpResponse:
    """To render a specific licence view.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        id (UUID): The id of the licence.

    Raises:
        Http404: If any exception occurs.

    Returns:
        HttpResponse: The rendered text/html view with context
    """
    try:
        try:
            license = License.get_cache_one(id=id)
        except:
            license = License.objects.get(id=id)
        return renderer(request, Template.Projects.LICENSE_LIC, dict(license=license))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def create(request: WSGIRequest) -> HttpResponse:
    """To render create project page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderer(request, Template.Projects.CREATE)


@normal_profile_required
@require_GET
def createFree(request: WSGIRequest) -> HttpResponse:
    """To render create free project page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    categories = Category.get_all().order_by('name')
    licenses = License.get_all()
    return renderer(request, Template.Projects.CREATE_FREE, dict(categories=categories, licenses=licenses))


@normal_profile_required
@require_GET
def createMod(request: WSGIRequest) -> HttpResponse:
    """To render create verified project page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    categories = Category.get_all().order_by('name')
    licenses = License.get_all()
    return renderer(request, Template.Projects.CREATE_MOD, dict(categories=categories, licenses=licenses))


@normal_profile_required
@require_GET
def createCore(request: WSGIRequest) -> HttpResponse:
    """To render create core project page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    categories = Category.get_all().order_by('name')
    licenses = License.objects.filter(
        creator=request.user.profile, public=False).order_by('name')
    return renderer(request, Template.Projects.CREATE_CORE, dict(categories=categories, licenses=licenses))


@normal_profile_required
@require_JSON
def validateField(request: WSGIRequest, field: str) -> JsonResponse:
    """To validate a field while creating project (primarily nickname validation)

    Args:
        request (WSGIRequest): The request object.
        field (str): The field to validate.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK, or main.strings.Code.NO with error message
    """
    try:
        data = request.POST[field]
        if field in ['reponame', 'nickname', 'codename']:
            if not uniqueRepoName(data):
                return respondJson(Code.NO, error=Message.Custom.already_exists(data))
            else:
                return respondJson(Code.OK)
        else:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def licences(request: WSGIRequest) -> JsonResponse:
    """(Deprecated?) To get the public licences excluding the received license IDs.
    """
    licenses = License.objects.filter(public=True, creator=Profile.KNOTBOT()).exclude(
        id__in=request.POST.get('givenlicenses', [])).values()
    return respondJson(Code.OK, dict(licenses=list(licenses)))


@normal_profile_required
@require_POST
@decode_JSON
def addLicense(request: WSGIRequest) -> JsonResponse:
    """ To add a custom license in database.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK, or main.strings.Code.NO with error message
    """
    try:
        name = request.POST['name'][:100].strip()
        description = request.POST['description'][:950].strip()
        content = request.POST['content'][:299950]
        public = request.POST.get('public', False)

        if not (name and description and content):
            raise KeyError(name, description, content)

        if License.objects.filter(name__iexact=str(name).strip()).exists():
            return respondJson(Code.NO, error=Message.Custom.already_exists(name))
        lic: License = License.objects.create(
            name=name,
            description=description,
            content=content,
            public=public,
            creator=request.user.profile
        )
        return respondJson(Code.OK, dict(license=dict(
            id=lic.get_id,
            name=lic.name,
            description=lic.description,
        )))
    except KeyError:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='10/m', block=True, method=(Code.POST))
def submitFreeProject(request: WSGIRequest) -> HttpResponse:
    """To submit a free project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the project page if created successfully, else to the create page.
    """
    projectobj = None
    alerted = False
    try:
        acceptedTerms = request.POST.get("acceptterms", False)
        if not acceptedTerms:
            return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.TERMS_UNACCEPTED)
        license = request.POST['license'][:50]
        name = str(request.POST["projectname"]).strip()
        description = str(request.POST["projectabout"]).strip()
        category = request.POST["projectcategory"][:50]
        nickname = str(request.POST.get("projectnickname", '')).strip()
        if not nickname or not uniqueRepoName(nickname):
            return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.NICKNAME_ALREADY_TAKEN)
        sociallinks = []
        for key in request.POST.keys():
            if str(key).startswith('sociallink'):
                link = str(request.POST[key]).strip()
                if link:
                    sociallinks.append(link)
        projectobj = createFreeProject(
            creator=request.user.profile, name=name,
            category=category, description=description, licenseID=license,
            nickname=nickname,
            sociallinks=sociallinks
        )
        if not projectobj:
            raise Exception(projectobj)
        try:
            imageData = request.POST['projectimage']
            imageFile = base64ToImageFile(imageData)
            if imageFile:
                projectobj.image = imageFile
            projectobj.save()
        except:
            pass
        alerted = True
        return redirect(projectobj.getLink(success=Message.FREE_PROJECT_CREATED))
    except KeyError:
        if projectobj and not alerted:
            projectobj.delete()
        return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.SUBMISSION_ERROR)
    except Exception as e:
        errorLog(e)
        if projectobj and not alerted:
            projectobj.delete()
        return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.SUBMISSION_ERROR)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='3/m', block=True, method=(Code.POST))
def submitProject(request: WSGIRequest) -> HttpResponse:
    """To submit a verified project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the modeartion view if created successfully, else to the create page.
    """
    projectobj = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        acceptedTerms = request.POST.get("acceptterms", False)
        if not acceptedTerms:
            if json_body:
                return respondJson(Code.NO, error=Message.TERMS_UNACCEPTED)
            return respondRedirect(APPNAME, URL.projects.createMod(step=3), error=Message.TERMS_UNACCEPTED)
        license = request.POST.get('license', None)
        if not license:
            if json_body:
                return respondJson(Code.NO, error=Message.LICENSE_UNSELECTED)
            return respondRedirect(APPNAME, URL.projects.createMod(step=3), error=Message.LICENSE_UNSELECTED)
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        category = request.POST["projectcategory"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["description"]
        referURL = request.POST.get("referurl", "")
        stale_days = int(request.POST.get("stale_days", 3))
        stale_days = stale_days if stale_days in range(1, 16) else 3
        useInternalMods = request.user.profile.is_manager and request.POST.get(
            "useInternalMods", False)

        if not uniqueRepoName(reponame):
            if json_body:
                return respondJson(Code.NO, error=Message.NICKNAME_ALREADY_TAKEN)
            return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.NICKNAME_ALREADY_TAKEN)
        projectobj = createProject(creator=request.user.profile, name=name,
                                   category=category, reponame=reponame, description=description, url=referURL, licenseID=license)
        if not projectobj:
            raise Exception('createProject: False')
        try:
            imageData = request.POST['projectimage']
            imageFile = base64ToImageFile(imageData)
            if imageFile:
                projectobj.image = imageFile
            projectobj.save()
        except:
            pass
        mod = requestModerationForObject(
            projectobj, APPNAME, userRequest, referURL, useInternalMods=useInternalMods, stale_days=stale_days)
        if not mod:
            projectobj.delete()
            if useInternalMods:
                if request.user.profile.management().total_moderators == 0:
                    if json_body:
                        return respondJson(Code.NO, error=Message.NO_INTERNAL_MODERATORS)
                    return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.NO_INTERNAL_MODERATORS)
            if json_body:
                return respondJson(Code.NO, error=Message.SUBMISSION_ERROR)
            return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.SUBMISSION_ERROR)
        else:
            sendProjectSubmissionNotification(projectobj)
            if json_body:
                return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
            return redirect(projectobj.getLink(alert=Message.SENT_FOR_REVIEW))
    except KeyError:
        if projectobj:
            projectobj.delete()
        if json_body:
            return respondJson(Code.NO, error=Message.SUBMISSION_ERROR)
        return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.SUBMISSION_ERROR)
    except Exception as e:
        if projectobj:
            projectobj.delete()
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.SUBMISSION_ERROR)
        return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.SUBMISSION_ERROR)


@manager_only
@require_POST
@ratelimit(key='user', rate='3/m', block=True, method=(Code.POST))
def submitCoreProject(request: WSGIRequest) -> HttpResponse:
    """To submit a core project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the moderation view if created successfully, else to the create view.
    """
    projectobj = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        acceptedTerms = request.POST.get("coreproject_acceptterms", False)
        if not acceptedTerms:
            if json_body:
                return respondJson(Code.NO, error=Message.TERMS_UNACCEPTED)
            return respondRedirect(APPNAME, URL.projects.createCore(), error=Message.TERMS_UNACCEPTED)

        name = str(request.POST["coreproject_projectname"]).strip()
        about = str(request.POST["coreproject_projectabout"]).strip()
        category_id = request.POST["coreproject_projectcategory"]
        codename = str(request.POST["coreproject_codename"]).strip()
        userRequest = request.POST["coreproject_projectdescription"]

        chosenModID = request.POST.get("coreproject_moderator_id", False)
        useInternalMods = request.POST.get(
            "coreproject_internal_moderator", False)

        referURL = request.POST.get("coreproject_referurl", "")
        budget = float(request.POST.get("coreproject_projectbudget", 0))
        stale_days = request.POST.get("coreproject_stale_days", 3)

        lic_id = request.POST.get("coreproject_license_id", None)

        if stale_days == '':
            stale_days = 3
        else:
            stale_days = int(stale_days) if int(
                stale_days) in range(1, 16) else 3
        useInternalMods = useInternalMods and request.user.profile.is_manager

        if not uniqueRepoName(codename):
            if json_body:
                return respondJson(Code.NO, error=Message.CODENAME_ALREADY_TAKEN)
            return respondRedirect(APPNAME, URL.Projects.CREATE_CORE, error=Message.CODENAME_ALREADY_TAKEN)

        chosenModerator = None
        if chosenModID:
            chosenModerator: Profile = Profile.objects.filter(
                user__id=chosenModID, is_moderator=True, is_active=True, suspended=False, to_be_zombie=False).first()
        if chosenModerator:
            useInternalMods = False
        license = None
        if lic_id:
            license = License.objects.get(
                id=lic_id, creator=request.user.profile, public=False)
        else:
            lic_name = str(
                request.POST["coreproject_license_name"][:100]).strip()
            lic_about = str(
                request.POST["coreproject_license_about"][:950]).strip()
            lic_cont = str(
                request.POST["coreproject_license_content"][:299950]).strip()
            license: License = License.objects.create(
                name=lic_name, description=lic_about, content=lic_cont, creator=request.user.profile, public=False)

        category = Category.get_cache_one(id=category_id)
        projectobj = createCoreProject(name=name, category=category, codename=codename,
                                       description=about, creator=request.user.profile, license=license, budget=budget)
        if not projectobj:
            raise Exception('createCoreProject: False')
        try:
            imageData = request.POST['coreproject_projectimage']
            imageFile = base64ToImageFile(imageData)
            if imageFile:
                projectobj.image = imageFile
            projectobj.save()
        except:
            pass
        mod = requestModerationForCoreProject(
            projectobj, userRequest, referURL, useInternalMods=useInternalMods, stale_days=stale_days, chosenModerator=chosenModerator)
        if not mod:
            projectobj.delete()
            if useInternalMods:
                if request.user.profile.management().total_moderators == 0:
                    if json_body:
                        return respondJson(Code.NO, error=Message.NO_INTERNAL_MODERATORS)
                    return respondRedirect(APPNAME, URL.Projects.CREATE_CORE, error=Message.NO_INTERNAL_MODERATORS)
            if json_body:
                return respondJson(Code.NO, error=Message.NO_MODERATORS_AVAILABLE)
            return respondRedirect(APPNAME, URL.Projects.CREATE_CORE, error=Message.NO_MODERATORS_AVAILABLE)
        else:
            coreProjectSubmissionNotification(projectobj)
            if json_body:
                return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
            return redirect(projectobj.getLink(alert=Message.SENT_FOR_REVIEW))
    except (KeyError, ObjectDoesNotExist) as e:
        if projectobj:
            projectobj.delete()
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        return respondRedirect(APPNAME, URL.Projects.CREATE_CORE, error=Message.INVALID_REQUEST)
    except Exception as e:
        if projectobj:
            projectobj.delete()
        if json_body:
            return respondJson(Code.NO, error=Message.SUBMISSION_ERROR)
        errorLog(e)
        return respondRedirect(APPNAME, URL.Projects.CREATE_CORE, error=Message.SUBMISSION_ERROR)


@normal_profile_required
@require_POST
@decode_JSON
def acceptTerms(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To accept the terms & conditions for an existing project.
    Can be used for revised terms & conditions as well.

    METHODS: POST

    Args:
        request (WSGIRequest): Django request object
        projID (UUID): Project ID

    Returns:
        HttpResponse: 301 redirect to the project page if successful
        HttpResponseNotFound: 404 if unsuccessful
        JsonResponse: 200 with Code.OK if successful
        JsonResponse: 200 with Code.NO if unsuccessful
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        project: BaseProject = BaseProject.objects.get(
            id=projID, acceptedTerms=True, creator=request.user.profile)
        project.acceptedTerms = True
        project.save()
        if json_body:
            return respondJson(Code.OK, message=Message.ACCEPTED_TERMS)
        return redirect(project.getLink(success=Message.TERMS_ACCEPTED))
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_JSON
def trashProject(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To trash a project.
    If the project is a core/verfied project, a deletion request process is initiated.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The Project ID to trash

    Raises:
        Http404: If any exception occurs

    Returns:
        HttpResponseRedirect: redirect to the project page if successful
        JsonResponse: response json object main.strings.Code.OK if successful else main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        project: BaseProject = BaseProject.objects.get(
            id=projID, creator=request.user.profile, trashed=False, is_archived=False, suspended=False)
        if project.is_not_free() and project.is_approved():
            action = request.POST['action']
            subproject = project.getProject(True)
            if not subproject:
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            if action == Action.CREATE:
                if not subproject.can_request_deletion():
                    return respondJson(Code.NO, error=Message.INVALID_REQUEST)
                if subproject.request_deletion():
                    if subproject.verified:
                        verProjectDeletionRequest(
                            subproject.current_del_request())
                    else:
                        coreProjectDeletionRequest(
                            subproject.current_del_request())
                    return respondJson(Code.OK)
                return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
            elif action == Action.REMOVE:
                if subproject.cancel_del_request():
                    return respondJson(Code.OK)
                return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        else:
            moved = project.getProject().moveToTrash()
            if moved and json_body:
                return respondJson(Code.OK)
            elif moved:
                return redirect(request.user.profile.getLink(alert=Message.PROJECT_DELETED))
            if json_body:
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            return redirect(project.getLink(alert=Message.ERROR_OCCURRED))

    except (KeyError, ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)


@require_GET
def profileBase(request: WSGIRequest, nickname: str) -> HttpResponseRedirect:
    """To redirect to the actual profile url of the project.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        nickname (str): The nickname of the project

    Returns:
        HttpResponseRedirect: redirect to the project page if successful
    """
    try:
        project: FreeProject = FreeProject.objects.filter(
            nickname=nickname, trashed=False, is_archived=False).first()
        if not project:
            project: Project = Project.objects.filter(
                reponame=nickname, trashed=False, is_archived=False).first()
            if not project:
                project: CoreProject = CoreProject.objects.get(
                    codename=nickname, trashed=False, is_archived=False)
        return redirect(project.get_link)
    except ObjectDoesNotExist:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def profileCore(request: WSGIRequest, codename: str) -> HttpResponse:
    """To the profile view of a core project.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        codename (str): The codename of the project

    Raises:
        Http404: If any exception occurs

    Returns:
        HttpResponse: The profile view of the project
        HttpResonseRedirect: If the project is not approved, and user is creator/moderator, redirect to the moderation view
    """
    try:
        try:
            data = coreProfileData(request, codename=codename)
            if not data:
                raise ObjectDoesNotExist(codename)
            return renderer(request, Template.Projects.PROFILE_CORE, data)
        except:
            if request.user.is_authenticated:
                coreproject: CoreProject = CoreProject.objects.get(
                    codename=codename, trashed=False, is_archived=False, status__in=[Code.MODERATION, Code.REJECTED])
                if coreproject.creator == request.user.profile or coreproject.moderator() == request.user.profile:
                    return redirect(coreproject.moderation(pendingOnly=True).getLink())
            raise ObjectDoesNotExist(codename)
    except (ObjectDoesNotExist, ValidationError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def profileFree(request: WSGIRequest, nickname: str) -> HttpResponse:
    """To the profile view of a quick/free project.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        nickname (str): The nickname of the project

    Raises:
        Http404: If any exception occurs

    Returns:
        HttpResponse: The profile view of the project
    """
    try:
        data = freeProfileData(request, nickname=nickname)
        if not data:
            raise ObjectDoesNotExist(nickname)
        return renderer(request, Template.Projects.PROFILE_FREE, data)
    except (ObjectDoesNotExist, ValidationError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def profileMod(request: WSGIRequest, reponame: str) -> HttpResponse:
    """To the profile view of a verified project.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        reponame (str): The reponame of the project

    Raises:
        Http404: If any exception occurs

    Returns:
        HttpResponse: The profile view of the project
        HttpResonseRedirect: If the project is not approved, and user is creator/moderator, redirect to the moderation view
    """
    try:
        try:
            data = verifiedProfileData(request, reponame=reponame)
            if not data:
                raise ObjectDoesNotExist(reponame)
            return renderer(request, Template.Projects.PROFILE_MOD, data)
        except Exception:
            if request.user.is_authenticated:
                project: Project = Project.objects.get(
                    reponame=reponame, trashed=False, is_archived=False, status__in=[Code.MODERATION, Code.REJECTED])
                if project.creator == request.user.profile or project.moderator() == request.user.profile:
                    return redirect(project.moderation(pendingOnly=True).getLink())
            raise
    except (ObjectDoesNotExist, ValidationError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    """To edit the profile of a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projectID (UUID): The id of the project
        section (str): The section to edit

    Raises:
        Http404: If any exception occurs

    Returns:
        HttpResponseRedirect: redirects to profile view of the project with relevant message
    """
    try:
        project: BaseProject = BaseProject.objects.get(
            id=projectID, trashed=False, is_archived=False, suspended=False)

        if section == 'pallete':
            if request.user.profile != project.creator:
                if request.user.profile != project.get_moderator():
                    raise ObjectDoesNotExist(request.user, project)
            changed = False
            try:
                base64Data = str(request.POST['projectimage'])
                imageFile = base64ToImageFile(base64Data)
                if imageFile:
                    project.image = imageFile
                    changed = True
            except:
                pass
            try:
                name = str(request.POST['projectname']).strip()
                about = str(request.POST['projectabout']).strip()
                if name != project.name:
                    project.name = name
                    changed = True
                if about != project.description:
                    project.description = about
                    changed = True
                if changed:
                    project.save()
                    return redirect(project.getLink(success=Message.PROFILE_UPDATED), permanent=True)
                return redirect(project.getLink(), permanent=True)
            except Exception as e:
                errorLog(e)
                return redirect(project.getLink(error=Message.ERROR_OCCURRED), permanent=True)
        elif section == "sociallinks":
            if request.user.profile != project.creator:
                if request.user.profile != project.get_moderator():
                    if not project.co_creators.filter(user=request.user).exists():
                        raise ObjectDoesNotExist(request.user, project)
            sociallinks = []
            for key in request.POST.keys():
                if str(key).startswith('sociallink'):
                    link = str(request.POST[key]).strip()
                    if link:
                        sociallinks.append(link)
            sociallinks = list(set(sociallinks))[:5]
            ProjectSocial.objects.filter(project=project).delete()
            if len(sociallinks) > 0:
                projectSocials = []
                for link in sociallinks:
                    projectSocials.append(
                        ProjectSocial(project=project, site=link))
                ProjectSocial.objects.bulk_create(projectSocials)
                return redirect(project.getLink(success=Message.PROFILE_UPDATED), permanent=True)
            else:
                return redirect(project.getLink(), permanent=True)
        elif section == "description":
            if project.is_core:
                newbudget = float(request.POST['projectbudget'])
                project = project.getProject(True)
                if newbudget < project.budget:
                    if project.is_approved():
                        return redirect(project.getLink(error=Message.INVALID_REQUEST), permanent=True)
                project.budget = newbudget
                project.save()
            return redirect(project.getLink(), permanent=True)
        return redirect(project.getLink(error=Message.ERROR_OCCURRED), permanent=True)
    except (ObjectDoesNotExist, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def manageAssets(request: WSGIRequest, projectID: UUID) -> JsonResponse:
    """To manage the assets of a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projectID (UUID): The id of the project
        request.POST.action: The action to perform (main.strings.Action)

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
    try:
        action = request.POST["action"][:50]
        project: BaseProject = BaseProject.objects.get(
            id=projectID, trashed=False, is_archived=False, suspended=False)

        if not project.can_edit_assets(request.user.profile):
            raise ObjectDoesNotExist(request.user, project)

        if action == Action.CREATE:
            if not project.can_add_assets():
                raise ObjectDoesNotExist(project)
            name = str(request.POST['filename'][:100]).strip()
            file = base64ToFile(
                request.POST['filedata'], request.POST.get("actualFilename"))
            public = request.POST.get('public', False)
            asset: Asset = Asset.objects.create(
                baseproject=project, name=name, file=file, public=public, creator=request.user.profile)
            return respondJson(Code.OK, dict(asset=dict(
                id=asset.id,
                name=asset.name
            )))
        elif action == Action.UPDATE:
            assetID = request.POST['assetID'][:50]
            name = str(request.POST.get('filename', "")[:100]).strip()
            public = request.POST.get('public', None)
            if name:
                done = Asset.objects.filter(id=assetID, baseproject=project).update(
                    name=name)
                if not done:
                    raise ObjectDoesNotExist(assetID, request.POST)
            elif public in [True, False]:
                done = Asset.objects.filter(id=assetID, baseproject=project, creator=request.user.profile).update(
                    public=public)
                if not done:
                    raise ObjectDoesNotExist(assetID, request.POST)
            else:
                raise KeyError(request.POST)
        elif action == Action.REMOVE:
            assetID = request.POST['assetID'][:50]
            Asset.objects.filter(id=assetID, baseproject=project).delete()
        else:
            raise KeyError(action)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def topicsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    """To search for topics for a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project
        request.POST.query (str): The query to search for

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and topics found, otherwise main.strings.Code.NO
    """
    try:
        query = str(request.POST['query'][:100]).strip()
        if not query:
            raise KeyError(query)

        limit = int(request.POST.get('limit', 5))
        project: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)

        if not project.can_edit_topics(request.user.profile):
            raise ObjectDoesNotExist(request.user, project)

        excluding = []
        if project:
            for topic in project.getTopics():
                excluding.append(topic.id)

        topics = Topic.objects.exclude(id__in=excluding).filter(
            Q(name__istartswith=query)
            | Q(name__iendswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[:limit]
        topicslist = []
        for topic in topics:
            topicslist.append(dict(
                id=topic.getID(),
                name=topic.name
            ))

        return respondJson(Code.OK, dict(
            topics=topicslist
        ))
    except (ObjectDoesNotExist, ValidationError, KeyError) as e:
        
        errorLog(e)
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def topicsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To update the topics of a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project
        request.POST.addtopicIDs (str): CSV of topic IDs
        request.POST.removetopicIDs (str): CSV of topic IDs
        request.POST.addtopics (str,list): CSV of topic names, or list of topic names if json body

    Raises:
        Http404: If the project does not exist, or invalid request

    Returns:
        HttpResponseRedirect: The redirect to the project page with relevant message
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
    json_body = request.POST.get("JSON_BODY", False)
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        addtopics = request.POST.get('addtopics', None)

        project: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)

        if not project.can_edit_topics(request.user.profile):
            raise ObjectDoesNotExist(request.user, project)

        if not (addtopicIDs or removetopicIDs or addtopics):
            if json_body:
                return respondJson(Code.NO, error=Message.NO_TOPICS_SELECTED)
            return redirect(project.getLink(error=Message.NO_TOPICS_SELECTED))

        if removetopicIDs:
            if not json_body:
                removetopicIDs = removetopicIDs.strip(',').split(',')
            ProjectTopic.objects.filter(
                project=project, topic__id__in=removetopicIDs).delete()

        if addtopicIDs:
            if not json_body:
                addtopicIDs = addtopicIDs.strip(',').split(',')
            if len(addtopicIDs) < 1:
                raise ObjectDoesNotExist(addtopicIDs, project)

            projtops = ProjectTopic.objects.filter(project=project)
            currentcount = projtops.count()
            if currentcount + len(addtopicIDs) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(project.getLink(error=Message.MAX_TOPICS_ACHEIVED))
            for topic in Topic.objects.filter(id__in=addtopicIDs):
                project.topics.add(topic)
                topic.tags.set(project.getTags())

        if addtopics and len(addtopics) > 0:
            count = ProjectTopic.objects.filter(project=project).count()
            if not json_body:
                addtopics = addtopics.strip(',').split(',')
            if count + len(addtopics) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(project.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            projecttopics = []
            for top in addtopics:
                topic = addTopicToDatabase(
                    top, request.user.profile, project.getTags())
                projecttopics.append(ProjectTopic(
                    topic=topic, project=project))
            if len(projecttopics) > 0:
                ProjectTopic.objects.bulk_create(projecttopics)

        if json_body:
            return respondJson(Code.OK, message=Message.TOPICS_UPDATED)
        return redirect(project.getLink(success=Message.TOPICS_UPDATED))
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_JSON
def tagsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    """To search for tags for a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project
        request.POST.query (str): The query to search for

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and tags found, otherwise main.strings.Code.NO
    """
    try:
        query = str(request.POST["query"][:100]).strip()
        if not query:
            raise KeyError(query)
        limit = int(request.POST.get("limit", 5))
        project: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)

        if not project.can_edit_tags(request.user.profile):
            raise ObjectDoesNotExist(request.user, project)

        excludeIDs = []
        if project:
            for tag in project.tags.all():
                excludeIDs.append(tag.id)

        tags = Tag.objects.exclude(id__in=excludeIDs).filter(
            Q(name__istartswith=query)
            | Q(name__iendswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[:limit]
        tagslist = []
        for tag in tags:
            tagslist.append(dict(
                id=tag.getID(),
                name=tag.name
            ))

        return respondJson(Code.OK, dict(
            tags=tagslist
        ))
    except (ObjectDoesNotExist, ValidationError, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def tagsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To update the tags of a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project
        request.POST.addtagIDs (str): CSV of tag IDs
        request.POST.removetagIDs (str): CSV of tag IDs
        request.POST.addtags (str,list): CSV of tag names, or list of topic names if json body

    Raises:
        Http404: If the project does not exist, or invalid request

    Returns:
        HttpResponseRedirect: The redirect to the project page with relevant message
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    next = None
    project = None
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        addtags = request.POST.get('addtags', None)
        removetagIDs = request.POST.get('removetagIDs', None)
        project: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)

        if not project.can_edit_tags(request.user.profile):
            raise ObjectDoesNotExist(request.user, project)

        next = request.POST.get('next', project.getLink())

        if not (addtagIDs or removetagIDs or addtags):
            return respondJson(Code.NO)

        if removetagIDs:
            if not json_body:
                removetagIDs = removetagIDs.strip(',').split(",")
            ProjectTag.objects.filter(
                project=project, tag__id__in=removetagIDs).delete()

        currentcount = ProjectTag.objects.filter(project=project).count()
        if addtagIDs:
            if not json_body:
                addtagIDs = addtagIDs.strip(',').split(",")
            if len(addtagIDs) < 1:
                if json_body:
                    return respondJson(Code.NO, error=Message.NO_TAGS_SELECTED)
                return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
            if currentcount + len(addtagIDs) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.MAX_TAGS_ACHEIVED))

            for tag in Tag.objects.filter(id__in=addtagIDs):
                project.tags.add(tag)
                for topic in project.getTopics():
                    topic.tags.add(tag)
            currentcount = currentcount + len(addtagIDs)

        if addtags:
            if not json_body:
                addtags = addtags.strip(',').split(",")
            if (currentcount + len(addtags)) <= 5:
                for addtag in addtags:
                    tag = addTagToDatabase(addtag, request.user.profile)
                    project.tags.add(tag)
                    for topic in project.getTopics():
                        topic.tags.add(tag)
                currentcount = currentcount + len(addtags)
            else:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.MAX_TAGS_ACHEIVED))

        if json_body:
            return respondJson(Code.OK)
        return redirect(next)
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if next:
            return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO)
        if next:
            return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
        raise Http404(e)


@normal_profile_required
@require_JSON
def userGithubRepos(request: WSGIRequest) -> JsonResponse:
    """To get the github repositories of a user.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The response with main.strings.Code.OK with repo list (id, name, taken:bool), otherwise main.strings.Code.NO
    """
    try:
        data = []
        if request.user.profile.is_manager():
            repos = request.user.profile.gh_org().get_repos('public')
        else:
            repos = request.user.profile.gh_user().get_repos('public')
        for repo in repos:
            taken = FreeRepository.objects.filter(repo_id=repo.id).exists() or Project.objects.filter(
                reponame=repo.name, status=Code.APPROVED, trashed=False, is_archived=False).exists() or CoreProject.objects.filter(codename=repo.name, status=Code.APPROVED, trashed=False, is_archived=False).exists()
            data.append(dict(name=repo.name, id=repo.id, taken=taken))
        return respondJson(Code.OK, dict(repos=data))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def linkFreeGithubRepo(request: WSGIRequest, projectID: UUID) -> JsonResponse:
    """To link a github repository to a free/quick project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projectID (UUID): The id of the project

    Returns:
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
    try:
        repoID = int(request.POST['repoID'])
        project: FreeProject = FreeProject.objects.get(
            id=projectID, creator=request.user.profile, trashed=False, is_archived=False, suspended=False)
        if FreeRepository.objects.filter(free_project=project).exists():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        ghuser = request.user.profile.gh_user()
        repo = request.user.profile.gh_api().get_repo(repoID)
        if not repo.private and repo.owner in [ghuser, request.user.profile.gh_org()] and not (
            FreeRepository.objects.filter(repo_id=repo.id).exists() or Project.objects.filter(reponame=repo.name, status=Code.APPROVED, trashed=False, is_archived=False).exists(
            ) or CoreProject.objects.filter(codename=repo.name, status=Code.APPROVED, trashed=False, is_archived=False).exists()
        ):
            FreeRepository.objects.create(
                free_project=project, repo_id=repo.id)
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def unlinkFreeGithubRepo(request: WSGIRequest, projectID: UUID) -> JsonResponse:
    """To unlink a github repository from a free/quick project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projectID (UUID): The id of the project

    Returns:
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
    try:
        project: FreeProject = FreeProject.objects.get(
            id=projectID, creator=request.user.profile, suspended=False)
        freerepo: FreeRepository = FreeRepository.objects.get(
            free_project=project)
        ghuser = request.user.profile.gh_user()
        repo = request.user.profile.gh_api().get_repo(int(freerepo.repo_id))
        if repo.owner in [ghuser, request.user.profile.gh_org()]:
            freerepo.delete()
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleAdmiration(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To toggle the admiration for a project.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project

    Returns:
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
        HttpResponseRedirect: If request method was not json POST.
    """
    project = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        admire = request.POST['admire']
        project: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)
        if admire in ["true", True]:
            project.admirers.add(request.user.profile)
        elif admire in ["false", False]:
            project.admirers.remove(request.user.profile)
        if json_body:
            return respondJson(Code.OK)
        return redirect(project.getLink())
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if project:
            return redirect(project.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if project:
            return redirect(project.getLink(error=Message.ERROR_OCCURRED))
        raise Http404(e)


@decode_JSON
def projectAdmirations(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To get the list of admirers for a project.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project

    Raises:
        Http404: If the project does not exist, or any other error occurs

    Returns:
        HttpResponse: The text/html reponse of admirers view with context
        JsonResponse: The response with main.strings.Code.OK and admirers list, otherwise main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        project: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)
        admirers = project.admirers.filter(is_active=True, suspended=False)
        if request.user.is_authenticated:
            admirers = request.user.profile.filterBlockedProfiles(admirers)
        if json_body:
            jadmirers = []
            for adm in admirers:
                jadmirers.append(
                    dict(
                        id=adm.get_userid,
                        name=adm.get_name,
                        dp=adm.get_dp,
                        url=adm.get_link,
                    )
                )
            return respondJson(Code.OK, dict(admirers=jadmirers))
        return render(request, Template().admirers, dict(admirers=admirers))
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@decode_JSON
def snapAdmirations(request: WSGIRequest, snapID: UUID) -> HttpResponse:
    """To get the list of admirers for a snapshot.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object
        snapID (UUID): The id of the snapshot

    Raises:
        Http404: If the snapshot does not exist, or any other error occurs

    Returns:
        HttpResponse: The text/html reponse of admirers view with context
        JsonResponse: The response with main.strings.Code.OK and admirers list, otherwise main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        snap: Snapshot = Snapshot.objects.get(
            id=snapID, suspended=False)
        admirers = snap.admirers.filter(is_active=True, suspended=False)
        if request.user.is_authenticated:
            admirers = request.user.profile.filterBlockedProfiles(admirers)
        if json_body:
            jadmirers = []
            for adm in admirers:
                jadmirers.append(
                    dict(
                        id=adm.get_userid,
                        name=adm.get_name,
                        dp=adm.get_dp,
                        url=adm.get_link,
                    )
                )
            return respondJson(Code.OK, dict(admirers=jadmirers))
        return render(request, Template().admirers, dict(admirers=admirers))
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleSnapAdmiration(request: WSGIRequest, snapID: UUID) -> JsonResponse:
    """To toggle the admiration for a snapshot.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        snapID (UUID): The id of the snapshot

    Returns:
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
    try:
        admire = request.POST['admire']
        snap: Snapshot = Snapshot.objects.get(
            id=snapID, base_project__trashed=False, base_project__is_archived=False, base_project__suspended=False)
        if admire in ["true", True]:
            snap.admirers.add(request.user.profile)
        elif admire in ["false", False]:
            snap.admirers.remove(request.user.profile)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


def liveData(request: WSGIRequest, projID: UUID) -> HttpResponse:
    """To get the thirdparty live data for a project.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The id of the project

    Raises:
        Http404: If the project does not exist, or any other error occurs

    Returns:
        JsonReponse: The response with main.strings.Code.OK and data (languages, contributors (html), commits (html)),
            otherwise main.strings.Code.NO
    """
    try:
        try:
            project: Project = Project.objects.get(
                id=projID, status=Code.APPROVED, trashed=False, is_archived=False, suspended=False)
        except:
            project: CoreProject = CoreProject.objects.get(
                id=projID, status=Code.APPROVED, trashed=False, is_archived=False, suspended=False)
        contributors, languages, commits = getProjectLiveData(project)
        contributorsHTML = renderString(request, Template.Projects.PROFILE_CONTRIBS, dict(
            contributors=contributors), APPNAME)
        commitsHTML = renderString(request, Template.Projects.PROFILE_COMMITS, dict(
            commits=commits), APPNAME)
        data = dict(
            languages=languages,
            contributorsHTML=str(contributorsHTML),
            commitsHTML=commitsHTML
        )
        return respondJson(Code.OK, data)
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@csrf_exempt
@github_bot_only
def githubBotEvents(request: WSGIRequest, botID: str) -> HttpResponse:
    """[Webhook] To receive github webhook events for knottersbot on github account actions.


    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        botID (str): The id of the bot

    Raises:
        Http404: If any error occurs

    Returns:
        HttpResponse: The text/plain response with main.strings.Code.OK
    """
    try:
        hookID = request.POST['id']
        event = request.POST['name']
        payload = request.POST['payload']
        ghapp: GhMarketApp = GhMarketApp.objects.get(gh_id=botID)
        hookrecord, _ = BotHookRecord.objects.get_or_create(
            hookID=hookID,
            ghmarketapp=ghapp,
            defaults=dict(
                success=False,
            )
        )
        if hookrecord.success:
            return HttpResponse(Code.NO)
        if event == "installation":
            action = payload['action']
            installation = payload['installation']
            account = installation['account']
            permissions = installation['permissions']
            frepos = FreeRepository.objects.filter(
                free_project__creator__githubID=account["login"])
            if action == 'created':
                repositories = payload['repositories']
                repo_ids = map(lambda r: r['id'], repositories)
                frepos = FreeRepository.objects.filter(repo_id__in=repo_ids)
                apprepos = []
                for frepo in frepos:
                    if not AppRepository.objects.filter(free_repo=frepo).exists():
                        apprepos.append(AppRepository(
                            free_repo=frepo,
                            gh_app=ghapp,
                            permissions=permissions
                        ))
                AppRepository.objects.bulk_create(apprepos)
            elif action == 'deleted':
                AppRepository.objects.filter(
                    free_repo__in=list(frepos), gh_app=ghapp).delete()
            elif action == 'suspend':
                AppRepository.objects.filter(free_repo__in=list(
                    frepos), gh_app=ghapp).update(suspended=True)
            elif action == 'unsuspend':
                AppRepository.objects.filter(free_repo__in=list(
                    frepos), gh_app=ghapp).update(suspended=False)
            elif action == 'new_permissions_accepted':
                AppRepository.objects.filter(free_repo__in=list(
                    frepos), gh_app=ghapp).update(permissions=permissions)
            else:
                raise Exception("Invalid action", event, action)
            hookrecord.success = True
            hookrecord.save()
        elif event == "installation_repositories":
            action = payload['action']
            installation = payload['installation']
            permissions = installation['permissions']
            account = installation['account']
            if action == 'added':
                repositories = payload['repositories_added']
                repo_ids = map(lambda r: r['id'], repositories)
                frepos = FreeRepository.objects.filter(repo_id__in=repo_ids)
                apprepos = []
                for frepo in frepos:
                    if not AppRepository.objects.filter(free_repo=frepo).exists():
                        apprepos.append(AppRepository(
                            free_repo=frepo,
                            gh_app=ghapp,
                            permissions=permissions
                        ))
                AppRepository.objects.bulk_create(apprepos)
            elif action == 'removed':
                repositories = payload['repositories_removed']
                repo_ids = map(lambda r: r['id'], repositories)
                frepos = FreeRepository.objects.filter(repo_id__in=repo_ids)
                AppRepository.objects.filter(
                    free_repo__in=list(frepos), gh_app=ghapp).delete()
            else:
                raise Exception("Invalid action", event, action)
            hookrecord.success = True
            hookrecord.save()
        else:
            repository = payload.get("repository", None)
            if not repository:
                return HttpResponseBadRequest(event)
            freeproject: FreeProject = (FreeRepository.objects.get(
                repo_id=repository["id"])).free_project
            addMethodToAsyncQueue(
                f"{APPNAME}.methods.{handleGithubKnottersRepoHook.__name__}", hookrecord.id, event, payload, freeproject.base())
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT:", e)
        raise Http404(e)


@csrf_exempt
@github_only
def githubEventsListener(request: WSGIRequest, type: str, projID: UUID) -> HttpResponse:
    """[Webhook] To receive github webhook events for a core/verified project repository.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        type (str): The type of the event
        projID (UUID): The id of the project

    Raises:
        Http404: If any error occurs

    Returns:
        HttpResponse: The text/plain response with main.strings.Code.OK
    """
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Invaild link type')
        ghevent = request.POST['ghevent']

        reponame = request.POST["repository"]["name"]
        owner_ghID = request.POST["repository"]["owner"]["login"]
        hookID = request.POST['hookID']
        if owner_ghID != PUBNAME:
            return HttpResponseBadRequest('Invalid owner')
        isCore = False
        try:
            project: Project = Project.objects.get(
                id=projID, reponame=reponame, trashed=False, is_archived=False, suspended=False)
        except Exception:
            try:
                project: CoreProject = CoreProject.objects.get(
                    id=projID, codename=reponame, trashed=False, is_archived=False, suspended=False)
                isCore = True
            except ObjectDoesNotExist:
                return HttpResponse(Code.NO)
            except Exception as e:
                errorLog("GH HOOK:", e)
                return HttpResponse(Code.NO)

        if isCore:
            hookrecord, _ = CoreProjectHookRecord.objects.get_or_create(hookID=hookID, defaults=dict(
                success=False,
                coreproject=project,
            ))
        else:
            hookrecord, _ = ProjectHookRecord.objects.get_or_create(hookID=hookID, defaults=dict(
                success=False,
                project=project,
            ))
        if hookrecord.success:
            return HttpResponse(Code.NO)
        postData = request.POST
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{handleGithubKnottersRepoHook.__name__}", hookrecord.id, ghevent, postData, project.base())
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT", e)
        raise Http404(e.__str__())


@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def browseSearch(request: WSGIRequest) -> HttpResponse:
    """To search for projects

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object

    Raises:
        Http404: If any error occurs

    Returns:
        HttpResponse: The text/html search view response with the search results context
        JsonResponse: The json response with main.strings.Code.OK and projects, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ""))[:100].strip()
        if not query:
            raise KeyError(query)
        limit = request.GET.get('limit', request.POST.get('limit', 10))
        excludecreatorIDs = []
        cachekey = f'project_browse_search_{query}{request.LANGUAGE_CODE}'
        if request.user.is_authenticated:
            excludecreatorIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}{''.join(excludecreatorIDs)}"

        projects = cache.get(cachekey, [])

        if not len(projects):
            specials = ('tag:', 'category:', 'topic:',
                        'creator:', 'license:', 'type:')
            verified = None
            core = None
            pquery = None
            dbquery = Q()
            invalidQuery = False
            if query.startswith(specials):
                def specquerieslist(q):
                    return [
                        Q(tags__name__iexact=q),
                        Q(category__name__iexact=q),
                        Q(topics__name__iexact=q),
                        Q(
                            Q(creator__user__first_name__iexact=q) | Q(creator__user__last_name__iexact=q) | Q(
                                creator__user__email__iexact=q) | Q(creator__nickname__iexact=q)
                        ),
                        Q(Q(license__name__iexact=q) | Q(
                            license__name__istartswith=q)),
                        Q()
                    ]
                commaparts = query.split(",")
                for cpart in commaparts:
                    if cpart.strip().lower().startswith(specials):
                        special, specialq = cpart.split(':')
                        if special.strip().lower() == 'type':
                            verified = specialq.strip().lower() == 'verified'
                            core = specialq.strip().lower() == 'core'
                            if not verified and not core:
                                invalidQuery = True
                                break
                        else:
                            dbquery = Q(dbquery, specquerieslist(specialq.strip())[
                                list(specials).index(f"{special.strip()}:")])
                    else:
                        pquery = cpart.strip()
                        break
            else:
                pquery = query
            if pquery and not invalidQuery:
                dbquery = Q(dbquery, Q(
                    Q(name__istartswith=pquery)
                    | Q(creator__user__first_name__istartswith=pquery)
                    | Q(creator__user__last_name__istartswith=pquery)
                    | Q(creator__user__email__istartswith=pquery)
                    | Q(creator__nickname__istartswith=pquery)
                    | Q(category__name__iexact=pquery)
                    | Q(topics__name__iexact=pquery)
                    | Q(tags__name__iexact=pquery)
                    | Q(category__name__istartswith=pquery)
                    | Q(topics__name__istartswith=pquery)
                    | Q(tags__name__istartswith=pquery)
                    | Q(license__name__istartswith=pquery)
                    | Q(name__icontains=pquery)
                    | Q(description__icontains=pquery)
                ))
            if not invalidQuery:
                projects: BaseProject = BaseProject.objects.exclude(trashed=True).exclude(
                    suspended=True).exclude(creator__user__id__in=excludecreatorIDs).filter(dbquery).distinct()[0:limit]
                if not len(projects):
                    projects: BaseProject = BaseProject.objects.exclude(trashed=True).exclude(suspended=True).exclude(creator__user__id__in=excludecreatorIDs).filter(
                        Q(co_creators__user__last_name__istartswith=pquery)
                        | Q(co_creators__user__email__istartswith=pquery)
                        | Q(co_creators__nickname__istartswith=pquery)
                    ).distinct()[:limit]

                if len(projects):
                    projects = list(
                        filter(lambda m: m.is_approved(), list(projects)))
                    if verified != None and verified:
                        projects = list(
                            filter(lambda m: m.is_verified(), list(projects)))
                    if core != None and core:
                        projects = list(
                            filter(lambda m: m.is_core(), list(projects)))
                    if len(projects):
                        cache.set(cachekey, projects, settings.CACHE_SHORT)

        if json_body:
            return respondJson(Code.OK, dict(
                projects=list(map(lambda m: dict(
                    id=m.get_id,
                    name=m.name, nickname=m.get_nickname(), is_verified=m.is_verified(),
                    url=m.get_abs_link, description=m.description,
                    imageUrl=m.get_abs_dp, creator=m.creator.get_name
                ), projects)),
                query=query
            ))

        return rendererstr(request, Template.Projects.BROWSE_SEARCH, dict(projects=projects, query=query))
    except (KeyError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def licenseSearch(request: WSGIRequest):
    """To search for licenses

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object

    Raises:
        Http404: If any error occurs

    Returns:
        HttpResponse: The text/html search view response with the search results context
        JsonResponse: The json response with main.strings.Code.OK and licenses, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ""))[
            :100].strip()

        if not query:
            raise KeyError(query)

        limit = request.GET.get('limit', request.POST.get('limit', 10))
        cachekey = f'license_search_{query}{request.LANGUAGE_CODE}'

        if request.user.is_authenticated:
            cachekey = f"{cachekey}{request.user.id}"

        licenses = cache.get(cachekey, [])
        if not len(licenses):
            licenses = License.objects.exclude(public=False).filter(Q(
                Q(name__istartswith=query)
                | Q(name__iexact=query)
                | Q(name__icontains=query)
                | Q(keyword__iexact=query)
                | Q(description__istartswith=query)
                | Q(description__icontains=query)
            ))[:limit]
            if len(licenses):
                cache.set(cachekey, licenses, settings.CACHE_SHORT)

        if json_body:
            return respondJson(Code.OK, dict(
                licenses=list(map(lambda l: dict(
                    id=l.get_id,
                    name=l.name,
                    keyword=l.keyword,
                    url=l.get_link,
                    description=l.description,
                    creator=l.creator.get_name
                ), licenses)),
                query=query
            ))
        return rendererstr(request, Template.Projects.LICENSE_SEARCH, dict(licenses=licenses, query=query))
    except (KeyError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@require_JSON
def snapshots(request: WSGIRequest, projID: UUID, limit: int) -> JsonResponse:
    """To get the snapshots view list for project's profile

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The project's id
        limit (int): The limit of the snapshots

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and snapshots (html) and their IDs, or main.strings.Code.NO
    """
    try:
        if not limit or limit < 1:
            limit = 10
        excludeIDs = request.POST.get('excludeIDs', [])

        cachekey = f"project_snapshots_{projID}_{limit}"

        if len(excludeIDs):
            cachekey = f"{cachekey}{''.join(excludeIDs)}"

        excludecreators = []
        if request.user.is_authenticated:
            excludecreators = request.user.profile.blockedProfiles()

        snaps = cache.get(cachekey, [])
        snapIDs = [snap.id for snap in snaps]

        if not len(snapIDs):
            snaps = Snapshot.objects.filter(base_project__id=projID, base_project__trashed=False,
                                            base_project__is_archived=False, base_project__suspended=False,
                                            suspended=False).exclude(id__in=excludeIDs).exclude(creator__in=excludecreators).order_by('-created_on')[:int(limit)]
            snapIDs = [snap.id for snap in snaps]
            cache.set(cachekey, snaps, settings.CACHE_INSTANT)
        return respondJson(Code.OK, dict(
            html=renderer_stronly(
                request, Template.Projects.SNAPSHOTS, dict(snaps=snaps)),
            snapIDs=snapIDs
        ))
    except (ValidationError, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def snapshot(request: WSGIRequest, projID: UUID, action: str) -> JsonResponse:
    """To create/update/remove a snapshot of a project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projID (UUID): The project's id
        action (str): The action to perform

    Raises:
        Http404: If any error occurs

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
        HttpResponseRedirect: Redirects to the project's profile with relevant message
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    baseproject = None
    try:
        baseproject: BaseProject = BaseProject.objects.get(
            id=projID, trashed=False, is_archived=False, suspended=False)
        if action == Action.CREATE:
            if not baseproject.can_post_snapshots(request.user.profile):
                raise ObjectDoesNotExist(request.user, baseproject)

            text = request.POST.get('snaptext', "")
            image = request.POST.get('snapimage', None)
            video = request.POST.get('snapvideo', None)
            if not (text or image or video):
                return redirect(baseproject.getLink(error=Message.INVALID_REQUEST))

            try:
                imagefile = base64ToImageFile(image)
            except:
                imagefile = None
            try:
                videofile = base64ToFile(video)
            except:
                videofile = None

            snapshot = Snapshot.objects.create(
                base_project=baseproject,
                creator=request.user.profile,
                text=text,
                image=imagefile,
                video=videofile
            )
            return redirect(baseproject.getProject().getLink(alert=Message.SNAP_CREATED))

        id = request.POST['snapid'][:50]
        snapshot: Snapshot = Snapshot.objects.get(
            id=id, base_project=baseproject, creator=request.user.profile)
        if action == Action.UPDATE:
            text = request.POST.get('snaptext', None)
            image = request.POST.get('snapimage', None)
            video = request.POST.get('snapvideo', None)
            if not (text or image or video):
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            changed = False
            if text and snapshot.text != text:
                snapshot.text = text
                changed = True
            if image or video:
                try:
                    newimgfile = base64ToImageFile(image)
                    snapshot.image.delete(save=False)
                    snapshot.image = newimgfile
                    changed = True
                except:
                    newimgfile = None
                if not newimgfile:
                    try:
                        newvidfile = base64ToFile(video)
                        snapshot.video.delete(save=False)
                        snapshot.video = newvidfile
                        changed = True
                    except:
                        newvidfile = None
            if changed:
                snapshot.save()
            return respondJson(Code.OK, message=Message.SNAP_UPDATED)

        if action == Action.REMOVE:
            snapshot.delete()
            return respondJson(Code.OK, message=Message.SNAP_DELETED)

        raise KeyError(action)
    except (ObjectDoesNotExist, KeyError, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if baseproject:
            return redirect(baseproject.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if baseproject:
            return redirect(baseproject.getLink(error=Message.INVALID_REQUEST))
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='1/s', block=True)
def reportCategories(request: WSGIRequest) -> JsonResponse:
    """To get the report categories

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and categories, or main.strings.Code.NO
    """
    try:
        reports = list(map(lambda r: dict(id=r[0], name=r[1]), list(ReportCategory.get_all().values_list("id", "name"))))
        return respondJson(Code.OK, dict(reports=reports))
    except Exception:
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def reportProject(request: WSGIRequest) -> JsonResponse:
    """To report a project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.report (UUID): The report category id
        request.POST.projectID (UUID): The project id

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        report = UUID(request.POST['report'][:50])
        projectID = UUID(request.POST['projectID'][:50])
        baseproject: BaseProject = BaseProject.objects.get(
            id=projectID, trashed=False, is_archived=False, suspended=False)
        category: ReportCategory = ReportCategory.get_cache_one(id=report)
        request.user.profile.reportProject(baseproject, category)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def reportSnapshot(request: WSGIRequest):
    """To report a snapshot

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.report (UUID): The report category id
        request.POST.snapID (UUID): The snapshot id

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        report = UUID(request.POST['report'][:50])
        snapID = UUID(request.POST['snapID'][:50])
        snapshot = Snapshot.objects.get(id=snapID, suspended=False)
        category: ReportCategory = ReportCategory.get_cache_one(id=report)
        request.user.profile.reportSnapshot(snapshot, category)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def handleOwnerInvitation(request: WSGIRequest) -> JsonResponse:
    """To handle ownership invitation creation/deletion

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.action (str): The action
        request.POST.projectID (UUID): The project id
        TODO: move projectID and/or action to the URL params.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        projID = request.POST['projectID'][:50]
        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            baseproject: BaseProject = BaseProject.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False, creator=request.user.profile)
            if not baseproject.can_invite_owner():
                raise ObjectDoesNotExist(
                    "Cannot invite owner for", baseproject)
            receiver = Profile.objects.get(
                user__email=email, suspended=False, is_active=True, to_be_zombie=False)
            if not baseproject.can_invite_owner_profile(receiver):
                raise InvalidUserOrProfile(receiver)

            inv, created = ProjectTransferInvitation.objects.get_or_create(
                baseproject=baseproject, sender=request.user.profile, resolved=False,
                defaults=dict(
                    receiver=receiver,
                    resolved=False
                )
            )

            if not created and inv.receiver == receiver:
                return respondJson(Code.NO, error=Message.ALREADY_INVITED)

            if not created:
                inv.receiver = receiver
                inv.expiresOn = timezone.now() + timedelta(days=1)
                inv.save()
            projectTransferInvitation(inv)
        elif action == Action.REMOVE:
            baseproject: BaseProject = BaseProject.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False, creator=request.user.profile)
            baseproject.cancel_invitation()
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, InvalidUserOrProfile, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def projectTransferInvite(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To render the project ownership transfer invitation view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the invitation is invalid, or any error occurs

    Returns:
        HttpResponse: The response text/html invitation view
    """
    try:
        invitation = ProjectTransferInvitation.objects.get(id=inviteID, baseproject__suspended=False,
                                                           baseproject__trashed=False, baseproject__is_archived=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        return renderer(request, Template.Projects.INVITATION,
                        dict(invitation=invitation))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@decode_JSON
def projectTransferInviteAction(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To handle the project ownership transfer invite action taken by receiver.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the request is invalid, or any error occurs

    Returns:
        HttpResponseRedirect: Redirect to project profile if action successful with relevant message.
    """
    try:
        action = request.POST['action'][:50]
        invitation = ProjectTransferInvitation.objects.get(
            id=inviteID, baseproject__suspended=False,
            baseproject__trashed=False, baseproject__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        if action == Action.ACCEPT:
            if invitation.accept():
                projectTransferAcceptedInvitation(invitation)
                return redirect(invitation.baseproject.getLink(alert=Message.PROJECT_TRANSFER_ACCEPTED))
        elif action == Action.DECLINE:
            if invitation.decline():
                projectTransferDeclinedInvitation(invitation)
                return redirect(invitation.baseproject.getLink(alert=Message.PROJECT_TRANSFER_DECLINED))
        else:
            raise ValidationError(action)
        return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_JSON
def handleVerModInvitation(request: WSGIRequest) -> JsonResponse:
    """To handle moderatorship invitation creation/deletion of a verified project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.action (str): The action
        request.POST.projectID (UUID): The project id
        TODO: move projectID and/or action to the URL params.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        projID = request.POST['projectID'][:50]

        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                raise ObjectDoesNotExist(email)
            project: Project = Project.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False)
            if project.moderator() != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            if not project.can_invite_mod():
                raise ObjectDoesNotExist("cannot invite mod: ", project)
            receiver = Profile.objects.get(
                user__email=email, is_moderator=True, suspended=False, is_active=True, to_be_zombie=False)
            if not project.can_invite_profile(receiver):
                raise InvalidUserOrProfile(receiver)

            if ProjectTransferInvitation.objects.filter(baseproject=project.base(), receiver=receiver).exists():
                return respondJson(Code.NO, error=Message.ALREADY_INVITED)
            inv, created = ProjectModerationTransferInvitation.objects.get_or_create(
                project=project,
                sender=request.user.profile,
                resolved=False,
                defaults=dict(
                    receiver=receiver,
                    resolved=False
                )
            )
            alert = True
            if not created:
                alert = False
                if inv.receiver != receiver:
                    inv.receiver = receiver
                    inv.expiresOn = timezone.now() + timedelta(days=1)
                    inv.save()
                    alert = True
                else:
                    return respondJson(Code.NO, error=Message.ALREADY_INVITED)
            if alert:
                projectModTransferInvitation(inv)
        elif action == Action.REMOVE:
            project: Project = Project.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False)
            if project.moderator() != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            project.cancel_moderation_invitation()
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, InvalidUserOrProfile):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@moderator_only
@require_GET
def projectModTransferInvite(request: WSGIRequest, inviteID: UUID):
    """To render the verified project moderatorship transfer invitation view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the invitation is invalid, or any error occurs

    Returns:
        HttpResponse: The response text/html invitation view
    """
    try:
        invitation = ProjectModerationTransferInvitation.objects.get(
            id=inviteID, project__suspended=False,
            project__trashed=False, project__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        return renderer(request, Template.Projects.VER_M_INVITATION,
                        dict(invitation=invitation))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_POST
@decode_JSON
def projectModTransferInviteAction(request: WSGIRequest, inviteID: UUID):
    """To handle the verified project moderatorship transfer invite action taken by receiver.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the request is invalid, or any error occurs

    Returns:
        HttpResponseRedirect: Redirect to project profile if action successful with relevant message.
    """
    try:
        action = request.POST['action'][:50]
        invitation = ProjectModerationTransferInvitation.objects.get(
            id=inviteID, project__suspended=False,
            project__trashed=False, project__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        if action == Action.ACCEPT:
            if invitation.accept():
                projectModTransferAcceptedInvitation(invitation)
                return redirect(invitation.project.getLink(alert=Message.PROJECT_MOD_TRANSFER_ACCEPTED))
        elif action == Action.DECLINE:
            if invitation.decline():
                projectModTransferDeclinedInvitation(invitation)
                return redirect(invitation.project.getLink(alert=Message.PROJECT_MOD_TRANSFER_DECLINED))
        else:
            raise ValidationError(action)
        return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_JSON
def handleCoreModInvitation(request: WSGIRequest):
    """To handle moderatorship invitation creation/deletion of a core project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.action (str): The action
        request.POST.projectID (UUID): The project id
        TODO: move projectID and/or action to the URL params.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        projID = request.POST['projectID'][:50]
        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                raise ObjectDoesNotExist(email)
            coreproject: CoreProject = CoreProject.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False)
            if coreproject.moderator() != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            if not coreproject.can_invite_mod():
                raise ObjectDoesNotExist("cannot invite mod: ", coreproject)
            receiver = Profile.objects.get(
                user__email=email, is_moderator=True, suspended=False, is_active=True, to_be_zombie=False)
            if not coreproject.can_invite_profile(receiver):
                raise InvalidUserOrProfile(receiver)

            if ProjectTransferInvitation.objects.filter(baseproject=coreproject.base(), receiver=receiver).exists():
                return respondJson(Code.NO, error=Message.ALREADY_INVITED)
            inv, created = CoreModerationTransferInvitation.objects.get_or_create(
                coreproject=coreproject,
                sender=request.user.profile,
                resolved=False,
                defaults=dict(
                    receiver=receiver,
                    resolved=False
                )
            )
            alert = True
            if not created:
                alert = False
                if inv.receiver != receiver:
                    inv.receiver = receiver
                    inv.expiresOn = timezone.now() + timedelta(days=1)
                    inv.save()
                    alert = True
                else:
                    return respondJson(Code.NO, error=Message.ALREADY_INVITED)
            if alert:
                coreProjectModTransferInvitation(inv)
        elif action == Action.REMOVE:
            coreproject: CoreProject = CoreProject.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False)
            if coreproject.moderator() != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            coreproject.cancel_moderation_invitation()
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@moderator_only
@require_GET
def coreProjectModTransferInvite(request: WSGIRequest, inviteID: UUID):
    """To render the core project moderatorship transfer invitation view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the invitation is invalid, or any error occurs

    Returns:
        HttpResponse: The response text/html invitation view
    """
    try:
        invitation = CoreModerationTransferInvitation.objects.get(
            id=inviteID, coreproject__suspended=False,
            coreproject__trashed=False, coreproject__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        return renderer(request, Template.Projects.CORE_M_INVITATION,
                        dict(invitation=invitation))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_JSON
def coreProjectModTransferInviteAction(request: WSGIRequest, inviteID: UUID):
    """To handle the core project moderatorship transfer invite action taken by receiver.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the request is invalid, or any error occurs

    Returns:
        HttpResponseRedirect: Redirect to project profile if action successful with relevant message.
    """
    try:
        action = request.POST['action'][:50]
        invitation = CoreModerationTransferInvitation.objects.get(
            id=inviteID, coreproject__suspended=False,
            coreproject__trashed=False, coreproject__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        if action == Action.ACCEPT:
            if invitation.accept():
                coreProjectModTransferAcceptedInvitation(invitation)
                return redirect(invitation.coreproject.getLink(alert=Message.PROJECT_MOD_TRANSFER_ACCEPTED))
        elif action == Action.DECLINE:
            if invitation.decline():
                coreProjectModTransferDeclinedInvitation(invitation)
                return redirect(invitation.coreproject.getLink(alert=Message.PROJECT_MOD_TRANSFER_DECLINED))
        else:
            raise ValidationError(action)
        return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_GET
def verProjectDeleteRequest(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To render the verified project deletion request view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the invitation is invalid, or any error occurs

    Returns:
        HttpResponse: The response text/html invitation view
    """
    try:
        invitation = VerProjectDeletionRequest.objects.get(
            id=inviteID, project__suspended=False,
            project__trashed=False, project__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        return renderer(request, Template.Projects.VER_DEL_INVITATION, dict(invitation=invitation))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_POST
@decode_JSON
def verProjectDeleteRequestAction(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To handle the verified project deletion request action taken by receiver (moderator).

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the request is invalid, or any error occurs

    Returns:
        HttpResponseRedirect: Redirect to project profile if action successful with relevant message.
    """
    try:
        action = request.POST['action'][:50]
        invitation = VerProjectDeletionRequest.objects.get(
            id=inviteID, project__suspended=False,
            project__trashed=False, project__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        if action == Action.ACCEPT:
            if invitation.accept():
                verProjectDeletionAcceptedRequest(invitation)
                addMethodToAsyncQueue(
                    f"{APPNAME}.methods.{deleteGhOrgVerifiedRepository.__name__}", invitation.project)
                return redirect(request.user.profile.getLink(alert=Message.PROJECT_DEL_ACCEPTED))
        elif action == Action.DECLINE:
            if invitation.decline():
                verProjectDeletionDeclinedRequest(invitation)
                return redirect(invitation.project.getLink(alert=Message.PROJECT_DEL_DECLINED))
        else:
            raise ValidationError(action)
        return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_GET
def coreProjectDeleteRequest(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To render the core project deletion request view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the invitation is invalid, or any error occurs

    Returns:
        HttpResponse: The response text/html invitation view
    """
    try:
        invitation = CoreProjectDeletionRequest.objects.get(
            id=inviteID, coreproject__suspended=False,
            coreproject__trashed=False, coreproject__is_archived=False, resolved=False,
            receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        return renderer(request, Template.Projects.CORE_DEL_INVITATION, dict(invitation=invitation))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_POST
@decode_JSON
def coreProjectDeleteRequestAction(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To handle the core project deletion request action taken by receiver (moderator).

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the request is invalid, or any error occurs

    Returns:
        HttpResponseRedirect: Redirect to project profile if action successful with relevant message.
    """
    try:
        action = request.POST['action'][:50]
        invitation = CoreProjectDeletionRequest.objects.get(
            id=inviteID, coreproject__suspended=False,
            coreproject__trashed=False, coreproject__is_archived=False,
            resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        if action == Action.ACCEPT:
            if invitation.accept():
                coreProjectDeletionAcceptedRequest(invitation)
                addMethodToAsyncQueue(
                    f"{APPNAME}.methods.{deleteGhOrgCoreepository.__name__}", invitation.coreproject)
                return redirect(request.user.profile.getLink(alert=Message.PROJECT_DEL_ACCEPTED))
        elif action == Action.DECLINE:
            if invitation.decline():
                coreProjectDeletionDeclinedRequest(invitation)
                return redirect(invitation.coreproject.getLink(alert=Message.PROJECT_DEL_DECLINED))
        else:
            raise ValidationError(action)
        return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def coreVerificationRequest(request: WSGIRequest) -> JsonResponse:
    """To handle verification request creation/deletion of a core project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.action (str): The action
        request.POST.projectID (UUID): The project id
        TODO: move projectID and/or action to the URL params.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        projID = request.POST['projectID'][:50]
        if action == Action.CREATE:
            coreproject: CoreProject = CoreProject.objects.get(
                id=projID, creator=request.user.profile, suspended=False, trashed=False, is_archived=False)
            if not coreproject.can_request_verification():
                raise ObjectDoesNotExist(
                    "cannot request verification: ", coreproject)

            if Project.objects.filter(reponame=coreproject.codename, creator=request.user.profile, status__in=[Code.MODERATION, Code.APPROVED], trashed=False, is_archived=False).exists():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)

            if CoreProjectVerificationRequest.objects.filter(coreproject=coreproject).exists():
                return respondJson(Code.NO, error=Message.ALREADY_EXISTS)

            # if not request.user.profile.has_ghID():
            #     return respondJson(Code.NO, error=Message.GH_ID_NOT_LINKED)

            requestData = request.POST['requestData'][:400]
            stale_days = int(request.POST.get("stale_days", 3))
            stale_days = stale_days if stale_days in range(
                1, 16) else coreproject.moderation().stale_days
            referURL = coreproject.get_abs_link

            verifiedproject = createConversionProjectFromCore(
                coreproject, request.POST['licenseID'])
            if not verifiedproject:
                raise Exception(verifiedproject)
            vreq = CoreProjectVerificationRequest.objects.create(
                coreproject=coreproject,
                verifiedproject=verifiedproject,
                resolved=False
            )
            if not vreq:
                raise Exception('err verrequest', vreq)
            verifiedproject.image = coreproject.image
            verifiedproject.topics.set(coreproject.topics.all())
            verifiedproject.tags.set(coreproject.tags.all())
            verifiedproject.save()
            done = assignModeratorToObject(APPNAME, verifiedproject, coreproject.moderator(),
                                           requestData, referURL, stale_days, internal_mod=coreproject.moderation().internal_mod)
            if not done:
                verifiedproject.delete()
                raise Exception('err verrequest moderation assign', done)
            sendProjectSubmissionNotification(verifiedproject)
            return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
        elif action == Action.REMOVE:
            coreproject: CoreProject = CoreProject.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False)
            if not coreproject.cancel_verification_request():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def freeVerificationRequest(request: WSGIRequest) -> JsonResponse:
    """To handle verification request creation/deletion of a free/quick project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.action (str): The action
        request.POST.projectID (UUID): The project id
        TODO: move projectID and/or action to the URL params.

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        projID = request.POST['projectID'][:50]
        if action == Action.CREATE:
            freeproject: FreeProject = FreeProject.objects.get(
                id=projID, creator=request.user.profile, suspended=False, trashed=False, is_archived=False)
            if not freeproject.can_request_verification():
                raise ObjectDoesNotExist(
                    "cannot request verification: ", freeproject)

            if Project.objects.filter(reponame=freeproject.nickname, creator=request.user.profile, status__in=[Code.MODERATION, Code.APPROVED], trashed=False, is_archived=False).exists():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)

            if FreeProjectVerificationRequest.objects.filter(freeproject=freeproject).exists():
                return respondJson(Code.NO, error=Message.ALREADY_EXISTS)

            if not request.user.profile.has_ghID():
                return respondJson(Code.NO, error=Message.GH_ID_NOT_LINKED)

            requestData = request.POST['requestData'][:300]
            stale_days = int(request.POST.get("stale_days", 3))
            stale_days = stale_days if stale_days in range(1, 16) else 3
            referURL = freeproject.get_abs_link

            useInternalMods = request.POST.get('useInternalMods', False)
            if useInternalMods and not request.user.profile.is_manager():
                useInternalMods = False

            verifiedproject = createConversionProjectFromFree(freeproject)
            if not verifiedproject:
                raise Exception(verifiedproject)
            vreq = FreeProjectVerificationRequest.objects.create(
                freeproject=freeproject,
                verifiedproject=verifiedproject,
                resolved=False
            )
            if not vreq:
                raise Exception('err verrequest', vreq)
            verifiedproject.image = freeproject.image
            verifiedproject.topics.set(freeproject.topics.all())
            verifiedproject.tags.set(freeproject.tags.all())
            verifiedproject.save()
            winnerVerification = request.POST.get('winnerVerification', False)

            mod = None
            if winnerVerification:
                subm = freeproject.submission()
                if subm and subm.is_winner():
                    mod = requestModerationForObject(
                        verifiedproject, APPNAME, requestData, referURL, stale_days=stale_days, chosenModerator=subm.competition.moderator)
            if not mod:
                mod = requestModerationForObject(
                    verifiedproject, APPNAME, requestData, referURL, useInternalMods=useInternalMods, stale_days=stale_days)
            if not mod:
                verifiedproject.delete()
                if useInternalMods:
                    if request.user.profile.management().total_moderators == 0:
                        return respondJson(Code.NO, error=Message.NO_INTERNAL_MODERATORS)
                raise Exception(
                    'error in verification request moderation assign', freeproject)
            else:
                sendProjectSubmissionNotification(verifiedproject)
                return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
        elif action == Action.REMOVE:
            freeproject: FreeProject = FreeProject.objects.get(
                id=projID, suspended=False, trashed=False, is_archived=False)
            if not freeproject.cancel_verification_request():
                raise ObjectDoesNotExist(freeproject)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, ValidationError, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def handleCocreatorInvitation(request: WSGIRequest, projectID: UUID) -> JsonResponse:
    """To handle cocreatorship invitation creation/deletion of a project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projectID (UUID): The project id
        request.POST.action (str): The action

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        if action == Action.CREATE:
            email = request.POST.get('email', "")[:100]
            if email:
                validate_email(email)
                if (request.user.email == email) or (email in request.user.emails()):
                    raise ObjectDoesNotExist(email)
                receiver: Profile = Profile.objects.get(
                    user__email=email, suspended=False, is_active=True, to_be_zombie=False)
            else:
                userID = UUID(request.POST['userID'][:50])
                receiver: Profile = Profile.objects.get(
                    user__id=userID, suspended=False, is_active=True, to_be_zombie=False)

            baseproject: BaseProject = BaseProject.objects.get(
                id=projectID, suspended=False, trashed=False, is_archived=False, creator=request.user.profile)
            if not baseproject.can_invite_cocreator():
                raise ObjectDoesNotExist(
                    "cannot invite cocreator: ", baseproject)
            if not baseproject.can_invite_cocreator_profile(receiver):
                raise InvalidUserOrProfile(receiver, baseproject)

            inv, created = BaseProjectCoCreatorInvitation.objects.get_or_create(
                base_project=baseproject,
                sender=request.user.profile,
                resolved=False,
                receiver=receiver,
                defaults=dict(
                    receiver=receiver,
                    resolved=False
                )
            )
            if not created:
                inv.expiresOn = timezone.now() + timedelta(days=1)
                inv.save()
            baseProjectCoCreatorInvitation(inv)
        elif action == Action.REMOVE:
            receiver_id = UUID(request.POST['receiver_id'][:50])
            baseproject: BaseProject = BaseProject.objects.get(
                id=projectID, suspended=False, trashed=False, is_archived=False, creator=request.user.profile)
            receiver = Profile.objects.get(user__id=receiver_id)
            baseproject.cancel_cocreator_invitation(receiver)
        elif action == Action.REMOVE_ALL:
            baseproject: BaseProject = BaseProject.objects.get(
                id=projectID, suspended=False, trashed=False, is_archived=False, creator=request.user.profile)
            baseproject.cancel_all_cocreator_invitations()
        else:
            raise ValidationError(action)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError, InvalidUserOrProfile):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def projectCocreatorInvite(request, inviteID):
    """To render the cocreatorship invitation view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the invitation is invalid, or any error occurs

    Returns:
        HttpResponse: The response text/html invitation view
    """
    try:
        invitation: BaseProjectCoCreatorInvitation = BaseProjectCoCreatorInvitation.objects.get(
            id=inviteID, receiver=request.user.profile, expiresOn__gt=timezone.now(),
            resolved=False, base_project__suspended=False,
            base_project__trashed=False, base_project__is_archived=False,
        )
        return renderer(request, Template.Projects.COCREATOR_INVITATION,
                        dict(invitation=invitation))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def projectCocreatorInviteAction(request, inviteID):
    """To handle the project cocreatorship invite action taken by receiver.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The invitation id

    Raises:
        Http404: If the request is invalid, or any error occurs

    Returns:
        HttpResponseRedirect: Redirect to project profile if action successful with relevant message.
    """
    try:
        action = request.POST['action'][:50]
        invitation = BaseProjectCoCreatorInvitation.objects.get(
            id=inviteID, base_project__suspended=False,
            base_project__trashed=False, base_project__is_archived=False,
            resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now()
        )
        if action == Action.ACCEPT:
            if invitation.accept():
                baseProjectCoCreatorAcceptedInvitation(invitation)
                return redirect(invitation.base_project.getLink(alert=Message.COCREATOR_INVITE_ACCEPTED))
        elif action == Action.DECLINE:
            if invitation.decline():
                baseProjectCoCreatorDeclinedInvitation(invitation)
                return redirect(invitation.base_project.getLink(alert=Message.COCREATOR_INVITE_DECLINED))
        else:
            raise ValidationError(action)
        return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def projectCocreatorManage(request: WSGIRequest, projectID: UUID) -> JsonResponse:
    """To manage existing co-creators

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        projectID (UUID): The project id

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action'][:50]
        cocreator_id = UUID(request.POST['cocreator_id'][:50])
        if action == Action.REMOVE:
            project: BaseProject = BaseProject.objects.get(
                Q(id=projectID, suspended=False, trashed=False, is_archived=False),
                Q(creator=request.user.profile)
                | Q(co_creators=request.user.profile))
            profile: Profile = project.co_creators.filter(
                user__id=cocreator_id).first()
            if not profile:
                raise InvalidUserOrProfile(profile)
            if not (profile == request.user.profile or project.creator == request.user.profile):
                raise InvalidUserOrProfile(request.user.profile)
            if not project.remove_cocreator(profile):
                raise ObjectDoesNotExist(profile, project)
        else:
            raise ValidationError(action)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, InvalidUserOrProfile):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
