from datetime import timedelta
import re
from uuid import UUID
from django.core.cache import cache
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query_utils import Q, InvalidQuery
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from moderation.views import action
from ratelimit.decorators import ratelimit
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect, render
from django.conf import settings
from main.bots import Github
from allauth.account.models import EmailAddress
from main.env import PUBNAME
from main.decorators import github_remote_only, manager_only, moderator_only, require_JSON_body, github_only, normal_profile_required, decode_JSON
from main.methods import addMethodToAsyncQueue, base64ToImageFile, base64ToFile,  errorLog, htmlmin, renderString, respondJson, respondRedirect
from main.strings import CORE_PROJECT, Action, Code, Event, Message, URL, Template, setURLAlerts
from moderation.models import Moderation
from moderation.methods import requestModerationForCoreProject, requestModerationForObject
from management.models import ReportCategory
from people.models import Profile, Topic
from .models import BaseProject, CoreModerationTransferInvitation, CoreProject, CoreProjectDeletionRequest, FileExtension, FreeProject, Asset, FreeRepository, License, Project, ProjectHookRecord, ProjectModerationTransferInvitation, ProjectSocial, ProjectTag, ProjectTopic, ProjectTransferInvitation, Snapshot, SnapshotAdmirer, Tag, Category, VerProjectDeletionRequest
from .mailers import coreProjectDeletionAcceptedRequest, coreProjectDeletionDeclinedRequest, coreProjectDeletionRequest, coreProjectModTransferAcceptedInvitation, coreProjectModTransferDeclinedInvitation, coreProjectModTransferInvitation, coreProjectSubmissionNotification, projectModTransferAcceptedInvitation, projectModTransferDeclinedInvitation, projectModTransferInvitation, projectTransferAcceptedInvitation, projectTransferDeclinedInvitation, projectTransferInvitation, sendProjectSubmissionNotification, verProjectDeletionAcceptedRequest, verProjectDeletionDeclinedRequest, verProjectDeletionRequest
from .methods import addTagToDatabase, createCoreProject, createFreeProject, deleteGhOrgCoreepository, deleteGhOrgVerifiedRepository, renderer, renderer_stronly, rendererstr, uniqueRepoName, createProject, getProjectLiveData
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


@require_GET
def licence(request: WSGIRequest, id: UUID) -> HttpResponse:
    try:
        license = License.objects.get(id=id)
        return renderer(request, Template.Projects.LICENSE_LIC, dict(license=license))
    except ObjectDoesNotExist as o:
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
    licenses = License.objects.filter(creator=Profile.KNOTBOT(),public=True).order_by('default')
    return renderer(request, Template.Projects.CREATE_FREE, dict(categories=categories, licenses=licenses))


@normal_profile_required
@require_GET
def createMod(request: WSGIRequest) -> HttpResponse:
    categories = Category.objects.all().order_by('name')
    licenses = License.objects.filter(creator=Profile.KNOTBOT(),public=True).order_by('default')
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
@ratelimit(key='user', rate='10/m', block=True, method=('POST'))
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
            raise Exception()
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
                if request.user.profile.management.total_moderators == 0:
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
                if request.user.profile.management.total_moderators == 0:
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
                 
    except (KeyError,ObjectDoesNotExist) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)


@require_GET
def profileCore(request: WSGIRequest, codename: str) -> HttpResponse:
    try:
        coreproject = CoreProject.objects.get(codename=codename, trashed=False, suspended=False)
        if coreproject.status == Code.APPROVED:
            iscreator = False if not request.user.is_authenticated else coreproject.creator == request.user.profile
            ismoderator = False if not request.user.is_authenticated else coreproject.moderator == request.user.profile
            if coreproject.suspended and not (iscreator or ismoderator):
                raise Exception()
            isAdmirer = request.user.is_authenticated and coreproject.isAdmirer(
                request.user.profile)
            return renderer(request, Template.Projects.PROFILE_CORE, dict(project=coreproject, iscreator=iscreator, ismoderator=ismoderator, isAdmirer=isAdmirer))
        else:
            if request.user.is_authenticated:
                mod = Moderation.objects.filter(coreproject=coreproject, type=CORE_PROJECT, status__in=[
                    Code.REJECTED, Code.MODERATION]).order_by('-respondOn','-requestOn').first()
                if coreproject.creator == request.user.profile or mod.moderator == request.user.profile:
                    return redirect(mod.getLink())
            raise Exception(codename)
    except ObjectDoesNotExist as e:
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
            raise Exception(nickname)
        isAdmirer = request.user.is_authenticated and project.isAdmirer(
            request.user.profile)
        return renderer(request, Template.Projects.PROFILE_FREE, dict(project=project, iscreator=iscreator, isAdmirer=isAdmirer))
    except ObjectDoesNotExist as e:
        return profileCore(request, nickname)
    except Exception as e:
        raise Http404(e)


@require_GET
def profileMod(request: WSGIRequest, reponame: str) -> HttpResponse:
    try:
        project = Project.objects.get(
            reponame=reponame, trashed=False, suspended=False)
        if project.status == Code.APPROVED:
            iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
            ismoderator = False if not request.user.is_authenticated else project.moderator == request.user.profile
            if project.suspended and not (iscreator or ismoderator):
                raise Exception()
            isAdmirer = request.user.is_authenticated and project.isAdmirer(
                request.user.profile)
            return renderer(request, Template.Projects.PROFILE_MOD, dict(project=project, iscreator=iscreator, ismoderator=ismoderator, isAdmirer=isAdmirer))
        else:
            if request.user.is_authenticated:
                mod = Moderation.objects.filter(project=project, type=APPNAME, status__in=[
                    Code.REJECTED, Code.MODERATION]).order_by('-requestOn').first()
                if project.creator == request.user.profile or mod.moderator == request.user.profile:
                    return redirect(mod.getLink())
            raise Exception(reponame)
    except ObjectDoesNotExist as e:
        return profileFree(request, reponame)
    except Exception as e:
        raise Http404(e)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    try:
        project = BaseProject.objects.get(
            id=projectID, creator=request.user.profile, trashed=False, suspended=False)
        project = project.getProject(True)
        if not project:
            raise Exception(f'{projectID} project not found')
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
        return redirect(project.getLink(error=Message.ERROR_OCCURRED), permanent=True)
    except ObjectDoesNotExist:
        return HttpResponseForbidden()
    except Exception as e:
        errorLog(e)
        return HttpResponseForbidden()


@normal_profile_required
@require_JSON_body
def manageAssets(request: WSGIRequest, projID: UUID, action: str) -> JsonResponse:
    try:
        project = BaseProject.objects.get(
            id=projID, creator=request.user.profile, trashed=False, suspended=False)
        project.is_approved
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
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
def topicsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)

        project = BaseProject.objects.get(
            id=projID, creator=request.user.profile)
        project = project.getProject(True)
        if not project:
            raise Exception(f'{projID} project not found')
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
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def topicsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    json_body = request.POST.get("JSON_BODY", False)
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        addtopics = request.POST.get('addtopics', None)

        project = BaseProject.objects.get(
            id=projID, creator=request.user.profile, trashed=False, suspended=False)
        project = project.getProject(True)
        if not project:
            raise Exception(f'{projID} project not found')

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
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404()


@normal_profile_required
@require_JSON_body
def tagsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)
        project = BaseProject.objects.get(
            id=projID, creator=request.user.profile)
        project = project.getProject(True)
        if not project:
            raise Exception(f'{projID} project not found')
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
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def tagsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    json_body = request.POST.get(Code.JSON_BODY, False)
    next = None
    project = None
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        addtags = request.POST.get('addtags', None)
        removetagIDs = request.POST.get('removetagIDs', None)
        project = BaseProject.objects.get(
            id=projID, creator=request.user.profile, trashed=False, suspended=False)
        project = project.getProject(True)
        if not project:
            raise Exception(f'{projID} project not found')

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
        ghuser = Github.get_user(request.user.profile.ghID)
        repos = ghuser.get_repos('public')
        data = []
        for repo in repos:
            taken = FreeRepository.objects.filter(repo_id=repo.id).exists()
            data.append({'name': repo.name, 'id': repo.id, 'taken': taken})
        return respondJson(Code.OK, dict(repos=data))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def linkFreeGithubRepo(request):
    try:
        repoID = int(request.POST['repoID'])
        project = FreeProject.objects.get(
            id=request.POST['projectID'], creator=request.user.profile, trashed=False, suspended=False)
        if FreeRepository.objects.filter(free_project=project).exists():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        ghuser = Github.get_user(request.user.profile.ghID)
        repo = Github.get_repo(repoID)
        if repo.owner == ghuser:
            FreeRepository.objects.create(free_project=project, repo_id=repoID)
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def unlinkFreeGithubRepo(request: WSGIRequest):
    try:
        project = FreeProject.objects.get(
            id=request.POST['projectID'], creator=request.user.profile, trashed=False, suspended=False)
        freerepo = FreeRepository.objects.get(free_project=project)
        ghuser = Github.get_user(request.user.profile.ghID)
        repo = Github.get_repo(int(freerepo.repo_id))
        if repo.owner == ghuser:
            freerepo.delete()
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def toggleAdmiration(request: WSGIRequest, projID: UUID):
    project = None
    try:
        project = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        if request.POST['admire'] in ["true", True]:
            project.admirers.add(request.user.profile)
        elif request.POST['admire'] in ["false", False]:
            project.admirers.remove(request.user.profile)
        if request.POST.get(Code.JSON_BODY, False):
            return respondJson(Code.OK)
        return redirect(project.getProject().getLink())
    except Exception as e:
        errorLog(e)
        if request.POST.get(Code.JSON_BODY, False):
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
            id=snapID, trashed=False, suspended=False)
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
        return renderer(request, Template.ADMIRERS, dict(admirers=admirers))
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
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
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
        project = Project.objects.get(
            id=projID, status=Code.APPROVED, trashed=False, suspended=False)
        data = cache.get(f"project_livedata_json_{projID}")
        if not data:
            contributors, languages = getProjectLiveData(project)
            contributorsHTML = renderString(request, Template.Projects.PROFILE_CONTRIBS, dict(
                contributors=contributors), APPNAME)
            data = dict(
                languages=languages,
                contributorsHTML=str(contributorsHTML),
            )
            cache.set(
                f"project_livedata_json_{projID}", data, settings.CACHE_SHORT)
        return respondJson(Code.OK, data)
    except Exception as e:
        errorLog(e)
        raise Http404()


@csrf_exempt
@github_remote_only
def githubEventsListenerFree(request: WSGIRequest, type: str, projID: UUID) -> HttpResponse:
    raise Http404()
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Invaild link type')
        event = request.POST['ghevent']
        reponame = request.POST["repository"]["name"]
        owner_ghID = request.POST["repository"]["owner"]["login"]
        hookID = request.POST['hookID']
        try:
            project = Project.objects.get(
                id=projID, reponame=reponame, trashed=False, suspended=False)
            if owner_ghID != PUBNAME:
                return HttpResponseBadRequest('Invalid owner')
        except Exception as e:
            errorLog(f"HOOK: {e}")
            return HttpResponse(Code.NO)
        hookrecord, _ = ProjectHookRecord.objects.get_or_create(hookID=hookID, defaults=dict(
            success=False,
            project=project,
        ))
        if hookrecord.success:
            return HttpResponse(Code.NO)
        if event == Event.PUSH:
            pusher = request.POST['pusher']
            committer = Profile.objects.filter(Q(Q(githubID=pusher['name']) | Q(
                user__email=pusher['email'])), is_active=True, to_be_zombie=False).first()
            if committer:
                committer.increaseXP(by=2)
                project.creator.increaseXP(by=2)
                project.moderator.increaseXP(by=2)
        elif event == Event.PR:
            pr = request.POST.get('pull_request', None)
            if pr:
                action = request.POST.get('action', None)
                pr_creator_ghID = pr['user']['login']
                if action == 'opened':
                    pr_creator = Profile.objects.filter(
                        githubID=pr_creator_ghID, is_active=True).first()
                    if pr_creator:
                        pr_creator.increaseXP(by=5)
                elif action == 'closed':
                    pr_creator = Profile.objects.filter(
                        githubID=pr_creator_ghID, is_active=True).first()
                    if pr['merged']:
                        if pr_creator:
                            pr_creator.increaseXP(by=10)
                        project.creator.increaseXP(by=5)
                        project.moderator.increaseXP(by=5)
                    else:
                        if pr_creator:
                            pr_creator.decreaseXP(by=2)
                elif action == 'reopened':
                    pr_creator = Profile.objects.filter(
                        githubID=pr_creator_ghID, is_active=True).first()
                    if pr_creator:
                        pr_creator.increaseXP(by=2)
                elif action == 'review_requested':
                    pr_reviewer = Profile.objects.filter(
                        githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if pr_reviewer:
                        pr_reviewer.increaseXP(by=5)
                elif action == 'review_request_removed':
                    pr_reviewer = Profile.objects.filter(
                        githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if pr_reviewer:
                        pr_reviewer.decreaseXP(by=5)
                else:
                    return HttpResponseBadRequest(event)
            else:
                return HttpResponseBadRequest(event)
        elif event == Event.STAR:
            action = request.POST.get('action', None)
            if action == 'created':
                project.creator.increaseXP(by=2)
                project.moderator.increaseXP(by=2)
            elif action == 'deleted':
                project.creator.decreaseXP(by=2)
                project.moderator.decreaseXP(by=2)
            else:
                return HttpResponseBadRequest(event)
        else:
            return HttpResponseBadRequest(event)
        hookrecord.success = True
        hookrecord.save()
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404()


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
        try:
            project = Project.objects.get(
                id=projID, reponame=reponame, trashed=False, suspended=False)
            if owner_ghID != PUBNAME:
                return HttpResponseBadRequest('Invalid owner')
        except Exception as e:
            errorLog(f"HOOK: {e}")
            return HttpResponse(Code.NO)
        hookrecord, _ = ProjectHookRecord.objects.get_or_create(hookID=hookID, defaults=dict(
            success=False,
            project=project,
        ))
        if hookrecord.success:
            return HttpResponse(Code.NO)
        if ghevent == Event.PUSH:
            commits = request.POST["commits"]
            committers = {}
            un_committers = []
            for commit in commits:
                commit_author_ghID = commit["author"]["username"]
                commit_author_email = commit["author"]["email"]
                if not un_committers.__contains__(commit_author_ghID):
                    commit_committer = committers.get(commit_author_ghID, None)
                    if not commit_committer:
                        commit_committer = Profile.objects.filter(Q(Q(githubID=commit_author_ghID) | Q(
                            user__email=commit_author_email)), is_active=True, suspended=False, to_be_zombie=False).first()
                        if not commit_committer:
                            emailaddr = EmailAddress.objects.filter(
                                email=commit_author_email, verified=True).first()
                            if not emailaddr:
                                un_committers.append(commit_author_ghID)
                                continue
                            else:
                                commit_committer = emailaddr.user.profile
                            committers[commit_author_ghID] = commit_committer
                        else:
                            committers[commit_author_ghID] = commit_committer
                    added = commit["added"]
                    removed = commit["removed"]
                    modified = commit["modified"]
                    changed = added + removed + modified
                    extensions = {}
                    for change in changed:
                        parts = change.split('.')
                        ext = parts[len(parts)-1]
                        extdic = extensions.get(ext, {})
                        fileext = extdic.get('fileext', None)
                        if not fileext:
                            fileext, _ = FileExtension.objects.get_or_create(
                                extension__iexact=ext, defaults=dict(extension=ext))
                            extensions[ext] = dict(fileext=fileext, topics=[])
                            fileext.topics.set(project.topics.all())
                        for topic in fileext.topics.all():
                            hastopic = False
                            increase = True
                            lastxp = 0
                            tpos = 0
                            if len(extensions[ext]['topics']) > 0:
                                for top in extensions[ext]['topics']:
                                    tpos = tpos + 1
                                    if top['topic'] == topic:
                                        hastopic = True
                                        lastxp = top['xp']
                                        if lastxp > 9:
                                            increase = False
                                        break

                            if increase:
                                by = 1
                                commit_committer.increaseTopicPoints(
                                    by=by, topic=topic)
                                if hastopic:
                                    extensions[ext]['topics'][tpos]['xp'] = lastxp+by
                                else:
                                    extensions[ext]['topics'].append(
                                        dict(topic=topic, xp=(lastxp+by)))
            project.creator.increaseXP(
                by=(((len(commits)//len(committers))//2) or 1))
            project.moderator.increaseXP(
                by=(((len(commits)//len(committers))//3) or 1))
        elif ghevent == Event.PR:
            pr = request.POST.get('pull_request', None)
            if pr:
                action = request.POST.get('action', None)
                pr_creator_ghID = pr['user']['login']
                if action == 'opened':
                    pr_creator = Profile.objects.filter(
                        githubID=pr_creator_ghID, is_active=True).first()
                    if pr_creator:
                        pr_creator.increaseXP(by=2)
                elif action == 'closed':
                    pr_creator = Profile.objects.filter(
                        githubID=pr_creator_ghID, is_active=True).first()
                    if pr['merged']:
                        if pr_creator:
                            pr_creator.increaseXP(by=3)
                        project.creator.increaseXP(by=2)
                        project.moderator.increaseXP(by=1)
                    else:
                        if pr_creator:
                            pr_creator.decreaseXP(by=2)
                elif action == 'reopened':
                    pr_creator = Profile.objects.filter(
                        githubID=pr_creator_ghID, is_active=True).first()
                    if pr_creator:
                        pr_creator.increaseXP(by=2)
                elif action == 'review_requested':
                    pr_reviewer = Profile.objects.filter(
                        githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if pr_reviewer:
                        pr_reviewer.increaseXP(by=4)
                elif action == 'review_request_removed':
                    pr_reviewer = Profile.objects.filter(
                        githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if pr_reviewer:
                        pr_reviewer.decreaseXP(by=3)
                else:
                    return HttpResponseBadRequest(ghevent)
            else:
                return HttpResponseBadRequest(ghevent)
        elif ghevent == Event.STAR:
            action = request.POST.get('action', None)
            if action == 'created':
                project.creator.increaseXP(by=2)
                project.moderator.increaseXP(by=1)
            elif action == 'deleted':
                project.creator.decreaseXP(by=2)
                project.moderator.decreaseXP(by=1)
            else:
                return HttpResponseBadRequest(ghevent)
        else:
            return HttpResponse(Code.UNKNOWN_EVENT)
        hookrecord.success = True
        hookrecord.save()
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404(e)


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
            excludecreatorIDs = request.user.profile.blockedIDs
            cachekey = f"{cachekey}{request.user.id}"

        projects = cache.get(cachekey,[])
        
        if not len(projects):
            
            specials = ('tag:', 'category:', 'topic:', 'creator:', 'type:')
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
                        Q()
                    ]
                commaparts = query.split(",")
                for cpart in commaparts:
                    if cpart.strip().lower().startswith(specials):
                        special, specialq = cpart.split(':')
                        if special.strip().lower() == 'type':
                            verified = specialq.strip().lower() == 'verified'
                            core = specialq.strip().lower() == 'core'
                            if not verified or not core:
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
                ))
            if not invalidQuery:
                projects = BaseProject.objects.exclude(trashed=True).exclude(
                    suspended=True).exclude(creator__user__id__in=excludecreatorIDs).filter(dbquery).order_by('name').distinct()[0:limit]
                projects = list(filter(lambda m: m.is_approved, list(projects)))
                if verified != None:
                    projects = list(filter(lambda m: verified ==
                                    m.is_verified, list(projects)))
                elif core != None:
                    projects = list(filter(lambda m: core ==
                                    m.is_core, list(projects)))

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
        return Http404(e)

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
        return Http404(e)

@require_JSON_body
def snapshots(request: WSGIRequest, projID: UUID, limit: int = 10):
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
            snaps = Snapshot.objects.filter(base_project__id=projID, base_project__trashed=False, base_project__suspended=False,suspended=False).exclude(id__in=excludeIDs).order_by('-created_on')[:limit]
            snapIDs = [snap.id for snap in snaps]
            if len(snaps):
                cache.set(cachekey, snaps, settings.CACHE_INSTANT)
        return respondJson(Code.OK, dict(
            html=htmlmin(renderer_stronly(request, Template.Projects.SNAPSHOTS, dict(snaps=snaps)), True),
            snapIDs=snapIDs
        ))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def snapshot(request: WSGIRequest, projID: UUID, action: str):
    json_body = request.POST.get(Code.JSON_BODY, False)
    baseproject = None
    try:
        baseproject = BaseProject.objects.get(
            id=projID, trashed=False, suspended=False)
        if action == Action.CREATE:
            if request.user.profile != baseproject.creator:
                if request.user.profile != baseproject.getProject().moderator:
                    raise Exception()
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
    except Exception as e:
        errorLog(e, False)
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
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
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
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
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
            if (request.user.email == email) or (email in request.user.emails):
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
    except ObjectDoesNotExist as o:
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
    except ObjectDoesNotExist as o:
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
            if (request.user.email == email) or (email in request.user.emails):
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
    except ObjectDoesNotExist as o:
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
    except ObjectDoesNotExist as o:
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
            if (request.user.email == email) or (email in request.user.emails):
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
    except ObjectDoesNotExist as o:
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
    except ObjectDoesNotExist as o:
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
