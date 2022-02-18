from datetime import timedelta
import re
from uuid import UUID
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query_utils import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import JsonResponse
from moderation.views import action
from ratelimit.decorators import ratelimit
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.conf import settings
from main.env import PUBNAME
from main.decorators import github_bot_only, manager_only, moderator_only, require_JSON_body, github_only, normal_profile_required, decode_JSON
from main.methods import addMethodToAsyncQueue, base64ToImageFile, base64ToFile,  errorLog, renderString, respondJson, respondRedirect
from main.strings import CORE_PROJECT, Action, Code, Event, Message, URL, Template, setURLAlerts
from moderation.models import Moderation
from moderation.methods import assignModeratorToObject, requestModerationForCoreProject, requestModerationForObject
from management.models import GhMarketApp, ReportCategory
from people.models import Profile, Topic
from .models import AppRepository, BaseProject, BotHookRecord, CoreModerationTransferInvitation, CoreProject, CoreProjectDeletionRequest, CoreProjectHookRecord, CoreProjectVerificationRequest, FileExtension, FreeProject, Asset, FreeProjectVerificationRequest, FreeRepository, License, Project, ProjectHookRecord, ProjectModerationTransferInvitation, ProjectSocial, ProjectTag, ProjectTopic, ProjectTransferInvitation, Snapshot, Tag, Category, VerProjectDeletionRequest
from .mailers import coreProjectDeletionAcceptedRequest, coreProjectDeletionDeclinedRequest, coreProjectDeletionRequest, coreProjectModTransferAcceptedInvitation, coreProjectModTransferDeclinedInvitation, coreProjectModTransferInvitation, coreProjectSubmissionNotification, projectModTransferAcceptedInvitation, projectModTransferDeclinedInvitation, projectModTransferInvitation, projectTransferAcceptedInvitation, projectTransferDeclinedInvitation, projectTransferInvitation, sendProjectSubmissionNotification, verProjectDeletionAcceptedRequest, verProjectDeletionDeclinedRequest, verProjectDeletionRequest
from .methods import addTagToDatabase, createConversionProjectFromCore, createConversionProjectFromFree, createCoreProject, createFreeProject, deleteGhOrgCoreepository, deleteGhOrgVerifiedRepository, handleGithubKnottersRepoHook, renderer, renderer_stronly, rendererstr, uniqueRepoName, createProject, getProjectLiveData
from .apps import APPNAME


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Projects.INDEX)


@require_GET
def allLicences(request: WSGIRequest) -> HttpResponse:
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
def public_licenses(request:WSGIRequest) -> HttpResponse:
    try:
        content = request.POST.get('content', False)
        licenses = License.objects.filter(creator=Profile.KNOTBOT(),public=True).order_by('-default')
        publices = []
        for l in licenses:
            if content:
                publices.append(dict(id=l.id, name=l.name, keyword=l.keyword, description=l.description, content=l.content))
            else:
                publices.append(dict(id=l.id, name=l.name, keyword=l.keyword, description=l.description,))
        return respondJson(Code.OK, dict(licenses=publices))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)

@require_GET
def licence(request: WSGIRequest, id: UUID) -> HttpResponse:
    try:
        license = License.objects.get(id=id)
        return renderer(request, Template.Projects.LICENSE_LIC, dict(license=license))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def create(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Projects.CREATE)


@normal_profile_required
@require_GET
def createFree(request: WSGIRequest) -> HttpResponse:
    categories = Category.objects.all().order_by('name')
    licenses = License.objects.filter(creator=Profile.KNOTBOT(),public=True).order_by('-default')
    return renderer(request, Template.Projects.CREATE_FREE, dict(categories=categories, licenses=licenses))


@normal_profile_required
@require_GET
def createMod(request: WSGIRequest) -> HttpResponse:
    categories = Category.objects.all().order_by('name')
    licenses = License.objects.filter(creator=Profile.KNOTBOT(),public=True).order_by('-default')
    return renderer(request, Template.Projects.CREATE_MOD, dict(categories=categories, licenses=licenses))

@normal_profile_required
@require_GET
def createCore(request: WSGIRequest) -> HttpResponse:
    categories = Category.objects.all().order_by('name')
    licenses = License.objects.filter(creator=request.user.profile,public=False).order_by('name')
    return renderer(request, Template.Projects.CREATE_CORE, dict(categories=categories,licenses=licenses))

@normal_profile_required
@require_JSON_body
def validateField(request: WSGIRequest, field: str) -> JsonResponse:
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
@require_JSON_body
def licences(request: WSGIRequest) -> JsonResponse:
    licenses = License.objects.filter(public=True, creator=Profile.KNOTBOT()).exclude(id__in=request.POST.get('givenlicenses', [])).values()
    return respondJson(Code.OK, dict(licenses=list(licenses)))


@normal_profile_required
@require_JSON_body
def addLicense(request: WSGIRequest) -> JsonResponse:
    name = request.POST.get('name', None)
    description = request.POST.get('description', None)
    content = request.POST.get('content', None)
    public = request.POST.get('public', False)

    if not (name and description and content):
        return respondJson(Code.NO, error=Message.INVALID_LIC_DATA)

    if License.objects.filter(name__iexact=str(name).strip()).exists():
        return respondJson(Code.NO, error=Message.Custom.already_exists(name))
    try:
        lic = License.objects.create(
            name=str(name).strip(),
            description=str(description).strip(),
            content=str(content),
            public=public,
            creator=request.user.profile
        )
        return respondJson(Code.OK, {'license': dict(
            id=lic.getID(),
            name=lic.name,
            description=lic.description,
        )})
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='10/m', block=True, method=(Code.POST))
def submitFreeProject(request: WSGIRequest) -> HttpResponse:
    projectobj = None
    alerted = False
    try:
        acceptedTerms = request.POST.get("acceptterms", False)
        if not acceptedTerms:
            return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.TERMS_UNACCEPTED)
        license = request.POST.get('license', None)
        if not license:
            return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.LICENSE_UNSELECTED)
        name = str(request.POST["projectname"]).strip()
        description = str(request.POST["projectabout"]).strip()
        category = request.POST["projectcategory"]
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
        stale_days = stale_days if stale_days in range(1,16) else 3
        useInternalMods = request.user.profile.is_manager and request.POST.get("useInternalMods", False)

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
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{sendProjectSubmissionNotification.__name__}", projectobj)
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
        useInternalMods = request.POST.get("coreproject_internal_moderator", False)

        referURL = request.POST.get("coreproject_referurl", "")
        budget = float(request.POST.get("coreproject_projectbudget", 0))
        stale_days = request.POST.get("coreproject_stale_days", 3)

        lic_id = request.POST.get("coreproject_license_id", None)
        
        if stale_days == '':
            stale_days = 3
        else:
            stale_days = int(stale_days) if int(stale_days) in range(1,16) else 3
        useInternalMods = useInternalMods and request.user.profile.is_manager

        if not uniqueRepoName(codename):
            if json_body:
                return respondJson(Code.NO, error=Message.CODENAME_ALREADY_TAKEN)
            return respondRedirect(APPNAME, URL.Projects.CREATE_CORE, error=Message.CODENAME_ALREADY_TAKEN)

        chosenModerator = None
        if chosenModID:
            chosenModerator = Profile.objects.filter(user__id=chosenModID, is_moderator=True,is_active=True,suspended=False,to_be_zombie=False).first()
        if chosenModerator:
            useInternalMods = False
        license = None
        if lic_id:
            license = License.objects.get(id=lic_id,creator=request.user.profile,public=False)
        else:
            lic_name = str(request.POST["coreproject_license_name"]).strip()
            lic_about = str(request.POST["coreproject_license_about"]).strip()
            lic_cont = str(request.POST["coreproject_license_content"]).strip()
            license = License.objects.create(name=lic_name, description=lic_about, content=lic_cont, creator=request.user.profile,public=False)

        category = Category.objects.get(id=category_id)
        projectobj = createCoreProject(name=name,category=category, codename=codename, description=about,creator=request.user.profile, license=license,budget=budget)
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
            projectobj, userRequest, referURL, useInternalMods=useInternalMods, stale_days=stale_days,chosenModerator=chosenModerator)
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
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{coreProjectSubmissionNotification.__name__}", projectobj)
            if json_body:
                return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
            return redirect(projectobj.getLink(alert=Message.SENT_FOR_REVIEW))
    except (KeyError,ObjectDoesNotExist) as e:
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
@require_JSON_body
def trashProject(request: WSGIRequest, projID: UUID) -> HttpResponse:
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        project = BaseProject.objects.get(
            id=projID, creator=request.user.profile, trashed=False, suspended=False)
        if project.is_not_free and project.is_approved:
            action = request.POST['action']
            subproject = project.getProject(True)
            if not subproject:
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            if action == Action.CREATE:
                if not subproject.can_request_deletion():
                    return respondJson(Code.NO, error=Message.INVALID_REQUEST)
                if subproject.request_deletion():
                    if subproject.verified:
                        addMethodToAsyncQueue(f"{APPNAME}.mailers.{verProjectDeletionRequest.__name__}", subproject.current_del_request())
                    else:
                        addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectDeletionRequest.__name__}", subproject.current_del_request())
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
                 
    except (KeyError,ObjectDoesNotExist,ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)


@require_GET
def profileBase(request: WSGIRequest, nickname: str) -> HttpResponse:
    try:
        project = FreeProject.objects.filter(nickname=nickname,trashed=False).first()
        if not project:
            project = Project.objects.filter(reponame=nickname,trashed=False).first()
            if not project:
                project = CoreProject.objects.get(codename=nickname,trashed=False)
        return redirect(project.get_link)
    except:
        raise Http404()

@require_GET
def profileCore(request: WSGIRequest, codename: str) -> HttpResponse:
    try:
        try:
            coreproject = CoreProject.objects.get(codename=codename, trashed=False, status=Code.APPROVED)
            iscreator = False if not request.user.is_authenticated else coreproject.creator == request.user.profile
            ismoderator = False if not request.user.is_authenticated else coreproject.moderator == request.user.profile
            if coreproject.suspended and not (iscreator or ismoderator):
                raise ObjectDoesNotExist('suspended', coreproject)
            isAdmirer = request.user.is_authenticated and coreproject.isAdmirer(
                request.user.profile)
            return renderer(request, Template.Projects.PROFILE_CORE, dict(project=coreproject, iscreator=iscreator, ismoderator=ismoderator, isAdmirer=isAdmirer))
        except:
            if request.user.is_authenticated:
                coreproject = CoreProject.objects.get(codename=codename, trashed=False, status__in=[Code.MODERATION,Code.REJECTED])
                mod = Moderation.objects.filter(coreproject=coreproject, type=CORE_PROJECT, status__in=[
                    Code.REJECTED, Code.MODERATION]).order_by('-respondOn','-requestOn').first()
                if coreproject.creator == request.user.profile or mod.moderator == request.user.profile:
                    return redirect(mod.getLink())
            raise ObjectDoesNotExist(codename)
    except (ObjectDoesNotExist,ValidationError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@require_GET
def profileFree(request: WSGIRequest, nickname: str) -> HttpResponse:
    try:
        project = FreeProject.objects.get(
            nickname=nickname, trashed=False, suspended=False)
        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        if project.suspended and not iscreator:
            raise ObjectDoesNotExist(nickname)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        return renderer(request, Template.Projects.PROFILE_FREE, dict(project=project, iscreator=iscreator, isAdmirer=isAdmirer))
    except (ObjectDoesNotExist,ValidationError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def profileMod(request: WSGIRequest, reponame: str) -> HttpResponse:
    try:
        try:
            project = Project.objects.get(
                reponame=reponame, trashed=False, status=Code.APPROVED)
            iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
            ismoderator = False if not request.user.is_authenticated else project.moderator == request.user.profile
            if project.suspended and not (iscreator or ismoderator):
                raise ObjectDoesNotExist()
            isAdmirer = request.user.is_authenticated and project.isAdmirer(
                request.user.profile)
            return renderer(request, Template.Projects.PROFILE_MOD, dict(project=project, iscreator=iscreator, ismoderator=ismoderator, isAdmirer=isAdmirer))
        except Exception as e:
            if request.user.is_authenticated:
                project = Project.objects.get(reponame=reponame, trashed=False, status__in=[Code.MODERATION,Code.REJECTED])
                mod = Moderation.objects.filter(project=project, type=APPNAME, status__in=[
                    Code.REJECTED, Code.MODERATION]).order_by('-requestOn').first()
                if project.creator == request.user.profile or mod.moderator == request.user.profile:
                    return redirect(mod.getLink())
            raise ObjectDoesNotExist(reponame)
    except (ObjectDoesNotExist,ValidationError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    try:
        bproject = BaseProject.objects.get(
            id=projectID, trashed=False, suspended=False)
        project = bproject.getProject(True)
        if not project:
            raise ObjectDoesNotExist(f'{projectID} project not found')
        if request.user.profile != project.creator:
            if request.user.profile != project.moderator:
                raise ObjectDoesNotExist()
        if section == 'pallete':
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
            if bproject.is_core:
                newbudget = float(request.POST['projectbudget'])
                if newbudget < project.budget:
                    if bproject.is_approved:
                        return redirect(project.getLink(error=Message.INVALID_REQUEST), permanent=True)
                project.budget = newbudget
                project.save()
            return redirect(project.getLink(), permanent=True)
        return redirect(project.getLink(error=Message.ERROR_OCCURRED), permanent=True)
    except (ObjectDoesNotExist,KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON_body
def manageAssets(request: WSGIRequest, projID: UUID, action: str) -> JsonResponse:
    try:
        project = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        sproject = project.getProject(True)
        if not sproject:
            raise ObjectDoesNotExist(f'{projID} project not found')
        if request.user.profile != project.creator:
            if request.user.profile != sproject.moderator:
                raise ObjectDoesNotExist()
        if action == Action.ADD:
            name = str(request.POST['filename']).strip()
            file = base64ToFile(request.POST['filedata'])
            public = request.POST.get('public', False)
            asset = Asset.objects.create(
                baseproject=project, name=name, file=file, public=public)
            return respondJson(Code.OK, dict(asset=dict(
                id=asset.id,
                name=asset.name
            )))
        elif action == Action.UPDATE:
            assetID = request.POST['assetID']
            name = str(request.POST['filename']).strip()
            public = request.POST['public']
            Asset.objects.filter(id=assetID, baseproject=project).update(
                name=name, public=public)
            return respondJson(Code.OK)
        elif action == Action.REMOVE:
            assetID = request.POST['assetID']
            Asset.objects.filter(id=assetID, baseproject=project).delete()
            return respondJson(Code.OK)
        else:
            return respondJson(Code.NO)
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
def topicsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)

        project = BaseProject.objects.get(
            id=projID, trashed=False)
        project = project.getProject(True)
        if not project:
            raise ObjectDoesNotExist(f'{projID} project not found')
        if request.user.profile != project.creator:
            if request.user.profile != project.moderator:
                raise ObjectDoesNotExist()
        excluding = []
        if project:
            for topic in project.getTopics():
                excluding.append(topic.id)

        topics = Topic.objects.exclude(id__in=excluding).filter(
            Q(name__istartswith=query)
            | Q(name__iendswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[0:5]
        topicslist = []
        for topic in topics:
            topicslist.append(dict(
                id=topic.getID(),
                name=topic.name
            ))

        return respondJson(Code.OK, dict(
            topics=topicslist
        ))
    except (ObjectDoesNotExist,ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def topicsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    json_body = request.POST.get("JSON_BODY", False)
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        addtopics = request.POST.get('addtopics', None)

        project = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        project = project.getProject(True)
        if not project:
            raise ObjectDoesNotExist(f'{projID} project not found')
        if request.user.profile != project.creator:
            if request.user.profile != project.moderator:
                raise ObjectDoesNotExist()
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
                if json_body:
                    return respondJson(Code.NO)
                return redirect(project.getLink())
            projtops = ProjectTopic.objects.filter(project=project)
            currentcount = projtops.count()
            if currentcount + len(addtopicIDs) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(project.getLink(error=Message.MAX_TOPICS_ACHEIVED))
            for topic in Topic.objects.filter(id__in=addtopicIDs):
                project.topics.add(topic)
                for tag in project.getTags:
                    topic.tags.add(tag)

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
                if len(top) > 35:
                    continue
                top = re.sub('[^a-zA-Z \\\s-]', '', top)
                if len(top) > 35:
                    continue
                topic, created = Topic.objects.get_or_create(name__iexact=top, defaults=dict(
                    name=str(top).capitalize(), creator=request.user.profile))
                if created:
                    for tag in project.getTags:
                        topic.tags.add(tag)
                projecttopics.append(ProjectTopic(
                    topic=topic, project=project))
            if len(projecttopics) > 0:
                ProjectTopic.objects.bulk_create(projecttopics)

        if json_body:
            return respondJson(Code.OK, message=Message.TOPICS_UPDATED)
        return redirect(project.getLink(success=Message.TOPICS_UPDATED))
    except (ObjectDoesNotExist,ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_JSON_body
def tagsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)
        project = BaseProject.objects.get(
            id=projID, trashed=False)
        project = project.getProject(True)
        if not project:
            raise ObjectDoesNotExist(f'{projID} project not found')
        if request.user.profile != project.creator:
            if request.user.profile != project.moderator:
                raise ObjectDoesNotExist()
        excludeIDs = []
        if project:
            for tag in project.tags.all():
                excludeIDs.append(tag.id)

        tags = Tag.objects.exclude(id__in=excludeIDs).filter(
            Q(name__istartswith=query)
            | Q(name__iendswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[0:5]
        tagslist = []
        for tag in tags:
            tagslist.append(dict(
                id=tag.getID(),
                name=tag.name
            ))

        return respondJson(Code.OK, dict(
            tags=tagslist
        ))
    except (ObjectDoesNotExist,ValidationError) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def tagsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    json_body = request.POST.get(Code.JSON_BODY, False)
    next = None
    project = None
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        addtags = request.POST.get('addtags', None)
        removetagIDs = request.POST.get('removetagIDs', None)
        project = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        project = project.getProject(True)
        if not project:
            raise ObjectDoesNotExist(f'{projID} project not found')
        if request.user.profile != project.creator:
            if request.user.profile != project.moderator:
                raise ObjectDoesNotExist()
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
                return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))

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
    except (ObjectDoesNotExist,ValidationError) as o:
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
@require_JSON_body
def userGithubRepos(request):
    try:
        data = []
        if request.user.profile.is_manager():
            repos = request.user.profile.gh_org().get_repos('public')
        else:
            repos = request.user.profile.gh_user().get_repos('public')
        for repo in repos:
            taken = FreeRepository.objects.filter(repo_id=repo.id).exists() or Project.objects.filter(reponame=repo.name,status=Code.APPROVED).exists() or CoreProject.objects.filter(codename=repo.name,status=Code.APPROVED).exists()
            data.append({'name': repo.name, 'id': repo.id, 'taken': taken})
        return respondJson(Code.OK, dict(repos=data))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def linkFreeGithubRepo(request):
    try:
        repoID = int(request.POST['repoID'])
        project = FreeProject.objects.get(
            id=request.POST['projectID'], creator=request.user.profile, trashed=False, suspended=False)
        if FreeRepository.objects.filter(free_project=project).exists():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        ghuser = request.user.profile.gh_user()
        repo = request.user.profile.gh_api().get_repo(repoID)
        if not repo.private and repo.owner in [ghuser, request.user.profile.gh_org()] and not (FreeRepository.objects.filter(repo_id=repo.id).exists() or Project.objects.filter(reponame=repo.name,status=Code.APPROVED).exists() or CoreProject.objects.filter(codename=repo.name,status=Code.APPROVED).exists()):
            FreeRepository.objects.create(free_project=project, repo_id=repo.id)
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def unlinkFreeGithubRepo(request: WSGIRequest):
    try:
        project = FreeProject.objects.get(
            id=request.POST['projectID'], creator=request.user.profile, trashed=False, suspended=False)
        freerepo = FreeRepository.objects.get(free_project=project)
        ghuser = request.user.profile.gh_user()
        repo = request.user.profile.gh_api().get_repo(int(freerepo.repo_id))
        if repo.owner in [ghuser, request.user.profile.gh_org()]:
            freerepo.delete()
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleAdmiration(request: WSGIRequest, projID: UUID):
    project = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        project = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        if request.POST['admire'] in ["true", True]:
            project.admirers.add(request.user.profile)
        elif request.POST['admire'] in ["false", False]:
            project.admirers.remove(request.user.profile)
        if json_body:
            return respondJson(Code.OK)
        return redirect(project.getProject().getLink())
    except (ObjectDoesNotExist,ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if project:
            return redirect(project.getProject().getLink(error=Message.ERROR_OCCURRED))
        raise Http404()

@decode_JSON
def projectAdmirations(request, projID):
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        project = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
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
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)

@decode_JSON
def snapAdmirations(request, snapID):
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        snap = Snapshot.objects.get(
            id=snapID,  suspended=False)
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
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)

@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleSnapAdmiration(request: WSGIRequest, snapID: UUID):
    snap = None
    try:
        snap = Snapshot.objects.get(
            id=snapID, base_project__trashed=False, base_project__suspended=False)
        if ["true", True].__contains__(request.POST['admire']):
            snap.admirers.add(request.user.profile)
        elif ["false", False].__contains__(request.POST['admire']):
            snap.admirers.remove(request.user.profile)
        return respondJson(Code.OK)
    except:
        return respondJson(Code.NO)


def liveData(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        try:
            project = Project.objects.get(
                id=projID, status=Code.APPROVED, trashed=False, suspended=False)
        except:
            project = CoreProject.objects.get(
                id=projID, status=Code.APPROVED, trashed=False, suspended=False)
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
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@csrf_exempt
@github_bot_only
def githubBotEvents(request: WSGIRequest, botID: str) -> HttpResponse:
    try:
        hookID = request.POST['id']
        event = request.POST['name']
        payload = request.POST['payload']
        ghapp = GhMarketApp.objects.get(gh_id=botID)
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
            frepos = FreeRepository.objects.filter(free_project__creator__githubID=account["login"])
            if action == 'created':
                repositories = payload['repositories']
                repo_ids = map(lambda r: r['id'] ,repositories)
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
                AppRepository.objects.filter(free_repo__in=list(frepos), gh_app=ghapp).delete()
            elif action == 'suspend':
                AppRepository.objects.filter(free_repo__in=list(frepos), gh_app=ghapp).update(suspended=True)
            elif action == 'unsuspend':
                AppRepository.objects.filter(free_repo__in=list(frepos), gh_app=ghapp).update(suspended=False)
            elif action == 'new_permissions_accepted':
                AppRepository.objects.filter(free_repo__in=list(frepos), gh_app=ghapp).update(permissions=permissions)
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
                repo_ids = map(lambda r: r['id'] ,repositories)
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
                repo_ids = map(lambda r: r['id'] ,repositories)
                frepos = FreeRepository.objects.filter(repo_id__in=repo_ids)
                AppRepository.objects.filter(free_repo__in=list(frepos), gh_app=ghapp).delete()
            else:
                raise Exception("Invalid action", event, action)
            hookrecord.success = True
            hookrecord.save()
        else:
            repository = payload.get("repository", None)
            if not repository:
                return HttpResponseBadRequest(event)
            freeproject = (FreeRepository.objects.get(repo_id=repository["id"])).free_project
            addMethodToAsyncQueue(f"{APPNAME}.methods.{handleGithubKnottersRepoHook.__name__}", hookrecord.id, event, payload, freeproject)
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404(e)


@csrf_exempt
@github_only
def githubEventsListener(request: WSGIRequest, type: str, projID: UUID) -> HttpResponse:
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
            project = Project.objects.get(
                id=projID, reponame=reponame, trashed=False, suspended=False)
        except Exception:
            try:
                project = CoreProject.objects.get(
                    id=projID, codename=reponame, trashed=False, suspended=False)
                isCore = True
            except ObjectDoesNotExist:
                return HttpResponse(Code.NO)
            except Exception as e:
                errorLog(f"HOOK: {e}")
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
        addMethodToAsyncQueue(f"{APPNAME}.methods.{handleGithubKnottersRepoHook.__name__}", hookrecord.id, ghevent, postData, project)
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404(e.__str__())


@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def browseSearch(request: WSGIRequest):
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ''))
        limit = request.GET.get('limit', request.POST.get('limit', 10))
        excludecreatorIDs = []
        cachekey = f'project_browse_search_{query}{request.LANGUAGE_CODE}'
        if request.user.is_authenticated:
            excludecreatorIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}{request.user.id}"

        projects = cache.get(cachekey,[])
        
        if not len(projects):    
            specials = ('tag:', 'category:', 'topic:', 'creator:', 'license:', 'type:')
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
                        Q(Q(creator__user__first_name__iexact=q)|Q(creator__user__last_name__iexact=q)|Q(creator__user__email__iexact=q)|Q(creator__githubID__iexact=q)),
                        Q(Q(license__name__iexact=q)|Q(license__name__istartswith=q)),
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
                    | Q(name__iendswith=pquery)
                    | Q(name__iexact=pquery)
                    | Q(name__icontains=pquery)
                    | Q(description__icontains=pquery)
                    | Q(creator__user__first_name__istartswith=pquery)
                    | Q(creator__user__last_name__istartswith=pquery)
                    | Q(creator__user__email__istartswith=pquery)
                    | Q(creator__githubID__istartswith=pquery)
                    | Q(creator__githubID__iexact=pquery)
                    | Q(category__name__iexact=pquery)
                    | Q(topics__name__iexact=pquery)
                    | Q(tags__name__iexact=pquery)
                    | Q(category__name__istartswith=pquery)
                    | Q(topics__name__istartswith=pquery)
                    | Q(tags__name__istartswith=pquery)
                    | Q(license__name__iexact=pquery)
                    | Q(license__name__istartswith=pquery)
                ))
            if not invalidQuery:
                projects = BaseProject.objects.exclude(trashed=True).exclude(
                    suspended=True).exclude(creator__user__id__in=excludecreatorIDs).filter(dbquery).distinct()[0:limit]
                projects = list(filter(lambda m: m.is_approved, list(projects)))
                if verified != None and verified:
                    projects = list(filter(lambda m: m.is_verified, list(projects)))
                if core != None and core:
                    projects = list(filter(lambda m: m.is_core, list(projects)))

                if len(projects):
                    cache.set(cachekey, projects, settings.CACHE_SHORT)
        
        if json_body:
            return respondJson(Code.OK, dict(
                projects=list(map(lambda m: dict(
                    id=m.get_id,
                    name=m.name, nickname=m.get_nickname, is_verified=m.is_verified,
                    url=m.get_abs_link, description=m.description,
                    imageUrl=m.get_abs_dp, creator=m.creator.get_name
                ), projects)),
                query=query
            ))
        
        return rendererstr(request, Template.Projects.BROWSE_SEARCH, dict(projects=projects, query=query))
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)

@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def licenseSearch(request: WSGIRequest):
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', '')
        limit = request.GET.get('limit', request.POST.get('limit', 10))
        cachekey = f'license_search_{query}{request.LANGUAGE_CODE}'

        if request.user.is_authenticated:
            cachekey = f"{cachekey}{request.user.id}"
        
        licenses = cache.get(cachekey,[])
        if not len(licenses):
            licenses = License.objects.exclude(public=False).filter(Q(
                Q(name__istartswith=query)
                | Q(name__iexact=query)
                | Q(name__icontains=query)
                | Q(keyword__iexact=query)
                | Q(description__istartswith=query)
                | Q(description__icontains=query)
            ))[0:limit]
            if len(licenses):
                cache.set(cachekey,licenses,settings.CACHE_SHORT)

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
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)

@require_JSON_body
def snapshots(request: WSGIRequest, projID: UUID, limit: int):
    # In Project Snapshot view
    try:
        if limit < 1:
            limit = 10
        excludeIDs = request.POST.get('excludeIDs', [])

        cachekey = f"project_snapshots_{projID}_{limit}"
        if len(excludeIDs):
            cachekey = cachekey + "".join(excludeIDs)
            
        snaps = cache.get(cachekey,[])
        snapIDs = [snap.id for snap in snaps]
        
        if not len(snaps):
            snaps = Snapshot.objects.filter(base_project__id=projID, base_project__trashed=False, base_project__suspended=False,suspended=False).exclude(id__in=excludeIDs).order_by('-created_on')[0:int(limit)]
            snapIDs = [snap.id for snap in snaps]
            if len(snaps):
                cache.set(cachekey, snaps, settings.CACHE_INSTANT)
        return respondJson(Code.OK, dict(
            html=renderer_stronly(request, Template.Projects.SNAPSHOTS, dict(snaps=snaps)),
            snapIDs=snapIDs
        ))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def snapshot(request: WSGIRequest, projID: UUID, action: str):
    json_body = request.POST.get(Code.JSON_BODY, False)
    baseproject = None
    try:
        baseproject = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        if action == Action.CREATE:
            if request.user.profile != baseproject.creator:
                if request.user.profile != baseproject.getProject().moderator:
                    raise ObjectDoesNotExist()
            text = request.POST.get('snaptext', None)
            image = request.POST.get('snapimage', None)
            video = request.POST.get('snapvideo', None)
            if not (text or image or video):
                return redirect(baseproject.getProject().getLink(error=Message.INVALID_REQUEST))

            try:
                imagefile = base64ToImageFile(image)
            except:
                imagefile = None
            try:
                videofile = base64ToImageFile(video)
            except:
                videofile = None
                

            snapshot = Snapshot.objects.create(
                base_project=baseproject,
                creator=request.user.profile,
                text=(text or ''),
                image=imagefile,
                video=videofile
            )
            return redirect(baseproject.getProject().getLink(alert=Message.SNAP_CREATED))

        id = request.POST['snapid']
        snapshot = Snapshot.objects.get(
            id=id, base_project=baseproject, creator=request.user.profile)
        if action == Action.UPDATE:
            text = request.POST.get('snaptext', None)
            image = request.POST.get('snapimage', None)
            video = request.POST.get('snapvideo', None)
            if not (text or image or video):
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            snapshot.text = text
            snapshot.save()
            return respondJson(Code.OK, message=Message.SNAP_UPDATED)

        if action == Action.REMOVE:
            snapshot.delete()
            return respondJson(Code.OK, message=Message.SNAP_DELETED)

        return respondJson(Code.NO)
    except ObjectDoesNotExist as o:
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


def reportCategories(request: WSGIRequest):
    try:
        categories = ReportCategory.objects.filter().order_by("name")
        reports = []
        for cat in categories:
            reports.append(dict(id=cat.id, name=cat.name))
        return respondJson(Code.OK, dict(reports=reports))
    except Exception as e:
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def reportProject(request: WSGIRequest):
    try:
        report = request.POST['report']
        projectID = request.POST['projectID']
        baseproject = BaseProject.objects.get(
            id=projectID, trashed=False, suspended=False)
        category = ReportCategory.objects.get(id=report)
        request.user.profile.reportProject(baseproject, category)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def reportSnapshot(request: WSGIRequest):
    try:
        report = request.POST['report']
        snapID = request.POST['snapID']
        snapshot = Snapshot.objects.get(id=snapID, suspended=False)
        category = ReportCategory.objects.get(id=report)
        request.user.profile.reportSnapshot(snapshot, category)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
def handleOwnerInvitation(request: WSGIRequest):
    try:
        action = request.POST['action']
        projID = request.POST['projectID']
        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            baseproject = BaseProject.objects.get(
                id=projID, suspended=False, trashed=False, creator=request.user.profile)
            if not baseproject.can_invite_owner():
                raise ObjectDoesNotExist("Cannot invite owner for", baseproject)
            receiver = Profile.objects.get(
                user__email=email, suspended=False, is_active=True, to_be_zombie=False)
            if not baseproject.can_invite_owner_profile(receiver):
                return respondJson(Code.NO, error=Message.USER_NOT_EXIST)

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
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectTransferInvitation.__name__}", inv)
        elif action == Action.REMOVE:
            baseproject = BaseProject.objects.get(
                id=projID, suspended=False, trashed=False, creator=request.user.profile)
            baseproject.cancel_invitation()
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def projectTransferInvite(request: WSGIRequest, inviteID: UUID):
    try:
        invitation = ProjectTransferInvitation.objects.get(id=inviteID, baseproject__suspended=False,
                                                           baseproject__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        return renderer(request, Template.Projects.INVITATION,
                 dict(invitation=invitation))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@normal_profile_required
@require_JSON_body
def projectTransferInviteAction(request: WSGIRequest, inviteID: UUID):
    try:
        action = request.POST['action']
        invitation = ProjectTransferInvitation.objects.get(id=inviteID, baseproject__suspended=False,
                                                           baseproject__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        done = False
        accept = False
        if action == Action.ACCEPT:
            accept = True
            done = invitation.accept()
        elif action == Action.DECLINE:
            done = invitation.decline()
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.PROJECT_TRANSFER_ACCEPTED 
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectTransferAcceptedInvitation.__name__}",invitation)
        else:
            message = Message.PROJECT_TRANSFER_DECLINED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectTransferDeclinedInvitation.__name__}",invitation)
        return redirect(invitation.baseproject.getLink(alert=message))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_JSON_body
def handleVerModInvitation(request: WSGIRequest):
    try:
        action = request.POST['action']
        projID = request.POST['projectID']
        
        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                raise ObjectDoesNotExist(email)
            project = Project.objects.get(id=projID, suspended=False, trashed=False)
            if project.moderator != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            if not project.can_invite_mod():
                raise ObjectDoesNotExist("cannot invite mod: ", project)
            receiver = Profile.objects.get(
                user__email=email, is_moderator=True, suspended=False, is_active=True, to_be_zombie=False)
            if not project.can_invite_profile(receiver):
                return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
            
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
                addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectModTransferInvitation.__name__}", inv)
        elif action == Action.REMOVE:
            project = Project.objects.get(id=projID, suspended=False, trashed=False)
            if project.moderator != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            project.cancel_moderation_invitation()
        return respondJson(Code.OK)
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@moderator_only
@require_GET
def projectModTransferInvite(request: WSGIRequest, inviteID: UUID):
    try:
        invitation = ProjectModerationTransferInvitation.objects.get(id=inviteID, project__suspended=False,
                                                           project__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        return renderer(request, Template.Projects.VER_M_INVITATION,
                 dict(invitation=invitation))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_JSON_body
def projectModTransferInviteAction(request: WSGIRequest, inviteID: UUID):
    try:
        action = request.POST['action']
        invitation = ProjectModerationTransferInvitation.objects.get(id=inviteID, project__suspended=False,
                                                           project__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        done = False
        accept = False
        if action == Action.ACCEPT:
            accept = True
            done = invitation.accept()
        elif action == Action.DECLINE:
            done = invitation.decline()
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.PROJECT_MOD_TRANSFER_ACCEPTED 
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectModTransferAcceptedInvitation.__name__}",invitation)
        else:
            message = Message.PROJECT_MOD_TRANSFER_DECLINED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{projectModTransferDeclinedInvitation.__name__}",invitation)
        return redirect(invitation.project.getLink(alert=message))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_JSON_body
def handleCoreModInvitation(request: WSGIRequest):
    try:
        action = request.POST['action']
        projID = request.POST['projectID']
        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                raise ObjectDoesNotExist(email)
            coreproject = CoreProject.objects.get(id=projID, suspended=False, trashed=False)
            if coreproject.moderator != request.user.profile:
                raise ObjectDoesNotExist(request.user.profile)
            if not coreproject.can_invite_mod():
                raise ObjectDoesNotExist("cannot invite mod: ", coreproject)
            receiver = Profile.objects.get(
                user__email=email, is_moderator=True, suspended=False, is_active=True, to_be_zombie=False)
            if not coreproject.can_invite_profile(receiver):
                return respondJson(Code.NO, error=Message.USER_NOT_EXIST)

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
                addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectModTransferInvitation.__name__}", inv)
        elif action == Action.REMOVE:
            coreproject = CoreProject.objects.get(id=projID, suspended=False, trashed=False)
            if coreproject.moderator != request.user.profile:
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
    try:
        invitation = CoreModerationTransferInvitation.objects.get(id=inviteID, coreproject__suspended=False,
                                                           coreproject__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        return renderer(request, Template.Projects.CORE_M_INVITATION,
                 dict(invitation=invitation))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_JSON_body
def coreProjectModTransferInviteAction(request: WSGIRequest, inviteID: UUID):
    try:
        action = request.POST['action']
        invitation = CoreModerationTransferInvitation.objects.get(id=inviteID, coreproject__suspended=False,
                                                           coreproject__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        done = False
        accept = False
        if action == Action.ACCEPT:
            accept = True
            done = invitation.accept()
        elif action == Action.DECLINE:
            done = invitation.decline()
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.PROJECT_MOD_TRANSFER_ACCEPTED 
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectModTransferAcceptedInvitation.__name__}",invitation)
        else:
            message = Message.PROJECT_MOD_TRANSFER_DECLINED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectModTransferDeclinedInvitation.__name__}",invitation)
        return redirect(invitation.coreproject.getLink(alert=message))
    except (ObjectDoesNotExist,ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_GET
def verProjectDeleteRequest(request, inviteID):
    try:
        invitation = VerProjectDeletionRequest.objects.get(id=inviteID, project__suspended=False,
                                                           project__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        return renderer(request, Template.Projects.VER_DEL_INVITATION, dict(invitation=invitation))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_JSON_body
def verProjectDeleteRequestAction(request, inviteID):
    try:
        action = request.POST['action']
        invitation = VerProjectDeletionRequest.objects.get(id=inviteID, project__suspended=False,
                                                           project__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        done = False
        accept = False
        if action == Action.ACCEPT:
            accept = True
            done = invitation.accept()
        elif action == Action.DECLINE:
            done = invitation.decline()
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.PROJECT_DEL_ACCEPTED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{verProjectDeletionAcceptedRequest.__name__}",invitation)
            addMethodToAsyncQueue(f"{APPNAME}.methods.{deleteGhOrgVerifiedRepository.__name__}",invitation.project)
            return redirect(request.user.profile.getLink(alert=message))
        else:
            message = Message.PROJECT_DEL_DECLINED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{verProjectDeletionDeclinedRequest.__name__}",invitation)
            return redirect(invitation.project.getLink(alert=message))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_GET
def coreProjectDeleteRequest(request, inviteID):
    try:
        invitation = CoreProjectDeletionRequest.objects.get(id=inviteID, coreproject__suspended=False,
                                                           coreproject__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        return renderer(request, Template.Projects.CORE_DEL_INVITATION, dict(invitation=invitation))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)

@moderator_only
@require_JSON_body
def coreProjectDeleteRequestAction(request, inviteID):
    try:
        action = request.POST['action']
        invitation = CoreProjectDeletionRequest.objects.get(id=inviteID, coreproject__suspended=False,
                                                           coreproject__trashed=False, resolved=False, receiver=request.user.profile, expiresOn__gt=timezone.now())
        done = False
        accept = False
        if action == Action.ACCEPT:
            accept = True
            done = invitation.accept()
        elif action == Action.DECLINE:
            done = invitation.decline()
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.PROJECT_DEL_ACCEPTED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectDeletionAcceptedRequest.__name__}",invitation)
            addMethodToAsyncQueue(f"{APPNAME}.methods.{deleteGhOrgCoreepository.__name__}",invitation.coreproject)
            return redirect(request.user.profile.getLink(alert=message))
        else:
            message = Message.PROJECT_DEL_DECLINED
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{coreProjectDeletionDeclinedRequest.__name__}",invitation)
            return redirect(invitation.coreproject.getLink(alert=message))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON_body
def coreVerificationRequest(request: WSGIRequest):
    try:
        action = request.POST['action']
        projID = request.POST['projectID']
        if action == Action.CREATE:
            coreproject = CoreProject.objects.get(id=projID,creator=request.user.profile, suspended=False, trashed=False)
            if not coreproject.can_request_verification():
                raise ObjectDoesNotExist("cannot request verification: ", coreproject)

            if Project.objects.filter(reponame=coreproject.codename, creator=request.user.profile, status__in=[Code.MODERATION,Code.APPROVED], trashed=False).exists():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)

            if CoreProjectVerificationRequest.objects.filter(coreproject=coreproject).exists():
                return respondJson(Code.NO, error=Message.ALREADY_EXISTS)

            if not request.user.profile.has_ghID():
                return respondJson(Code.NO, error=Message.GH_ID_NOT_LINKED)

            requestData = request.POST['requestData']
            stale_days = int(request.POST.get("stale_days", 3))
            stale_days = stale_days if stale_days in range(1,16) else coreproject.moderation.stale_days
            referURL = coreproject.get_abs_link

            verifiedproject = createConversionProjectFromCore(coreproject, request.POST['licenseID'])
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
            done = assignModeratorToObject(APPNAME,verifiedproject, coreproject.moderator, requestData,referURL,stale_days, internal_mod=coreproject.moderation.internal_mod)
            if not done:
                verifiedproject.delete()
                raise Exception('err verrequest moderation assign', done)
            addMethodToAsyncQueue(f"{APPNAME}.mailers.{sendProjectSubmissionNotification.__name__}", verifiedproject)
            return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
        elif action == Action.REMOVE:
            coreproject = CoreProject.objects.get(id=projID, suspended=False, trashed=False)
            if not coreproject.cancel_verification_request():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)

@normal_profile_required
@require_JSON_body
def freeVerificationRequest(request: WSGIRequest):
    try:
        action = request.POST['action']
        projID = request.POST['projectID']
        if action == Action.CREATE:
            freeproject = FreeProject.objects.get(id=projID,creator=request.user.profile, suspended=False, trashed=False)
            if not freeproject.can_request_verification():
                raise ObjectDoesNotExist("cannot request verification: ", freeproject)

            if Project.objects.filter(reponame=freeproject.nickname, creator=request.user.profile, status__in=[Code.MODERATION,Code.APPROVED], trashed=False).exists():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)

            if FreeProjectVerificationRequest.objects.filter(freeproject=freeproject).exists():
                return respondJson(Code.NO, error=Message.ALREADY_EXISTS)

            if not request.user.profile.has_ghID():
                return respondJson(Code.NO, error=Message.GH_ID_NOT_LINKED)

            requestData = request.POST['requestData']
            stale_days = int(request.POST.get("stale_days", 3))
            stale_days = stale_days if stale_days in range(1,16) else 3
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
                    mod = requestModerationForObject(verifiedproject, APPNAME, requestData, referURL, stale_days=stale_days, chosenModerator=subm.competition.moderator)
            if not mod:
                mod = requestModerationForObject(verifiedproject, APPNAME, requestData, referURL, useInternalMods=useInternalMods, stale_days=stale_days)
            if not mod:
                verifiedproject.delete()
                if useInternalMods:
                    if request.user.profile.management().total_moderators == 0:
                        return respondJson(Code.NO, error=Message.NO_INTERNAL_MODERATORS)
                raise Exception('err verrequest moderation assign', mod)
            else:
                addMethodToAsyncQueue(
                    f"{APPNAME}.mailers.{sendProjectSubmissionNotification.__name__}", verifiedproject)
                return respondJson(Code.OK, error=Message.SENT_FOR_REVIEW)
        elif action == Action.REMOVE:
            freeproject = FreeProject.objects.get(id=projID, suspended=False, trashed=False)
            if not freeproject.cancel_verification_request():
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
