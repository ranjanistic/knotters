from uuid import UUID
from itertools import chain
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings
# from django.views.decorators.cache import cache_page
from main.env import PUBNAME
from main.decorators import require_JSON_body, github_only, normal_profile_required
from main.methods import addMethodToAsyncQueue, base64ToImageFile, errorLog, renderString, respondJson, respondRedirect
from main.strings import Code, Event, Message, URL, Template
from moderation.models import Moderation
from moderation.methods import requestModerationForObject
from people.models import Profile, Topic
from .models import BaseProject, FreeProject, License, Project, ProjectHookRecord, ProjectTag, ProjectTopic, Tag, Category
from .mailers import freeProjectCreated, sendProjectSubmissionNotification
from .methods import createFreeProject, renderer, rendererstr, uniqueRepoName, createProject, getProjectLiveData
from .apps import APPNAME


@require_GET
# @cache_page(settings.CACHE_LONG)
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Projects.INDEX)


@require_GET
def allLicences(request: WSGIRequest) -> HttpResponse:
    try:
        alllicenses = License.objects.filter()
        public = alllicenses.filter(public=True)
        custom = []
        if request.user.is_authenticated:
            custom = alllicenses.filter(
                public=False, creator=request.user.profile)
        return renderer(request, Template.Projects.LICENSE_INDEX, dict(licenses=public, custom=custom))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
# @cache_page(settings.CACHE_LONG)
def licence(request: WSGIRequest, id: UUID) -> HttpResponse:
    try:
        license = License.objects.get(id=id)
        return renderer(request, Template.Projects.LICENSE_LIC, dict(license=license))
    except:
        raise Http404()

@normal_profile_required
@require_GET
def create(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Projects.CREATE)

@normal_profile_required
@require_GET
def createFree(request: WSGIRequest) -> HttpResponse:
    categories = Category.objects.all()
    licenses = License.objects.filter(Q(creator=request.user.profile) | Q(public=True))[0:5]
    return renderer(request, Template.Projects.CREATE_FREE, dict(categories=categories, licenses=licenses))
    
@normal_profile_required
@require_GET
def createMod(request: WSGIRequest) -> HttpResponse:
    categories = Category.objects.all()
    licenses = License.objects.filter(Q(creator=request.user.profile) | Q(public=True))[0:5]
    return renderer(request, Template.Projects.CREATE_MOD, dict(categories=categories, licenses=licenses))


@normal_profile_required
@require_JSON_body
def validateField(request: WSGIRequest, field: str) -> JsonResponse:
    try:
        data = request.POST[field]
        if field == 'reponame':
            if not uniqueRepoName(data):
                return respondJson(Code.NO, error=Message.Custom.already_exists(data))
            else:
                return respondJson(Code.OK)
        else:
            return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
def licences(request: WSGIRequest) -> JsonResponse:
    licenses = License.objects.filter(
        ~Q(id__in=request.POST.get('givenlicenses', []))).values()
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
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        category = request.POST["projectcategory"]
        nickname = request.POST.get("projectnickname",None)
        if not uniqueRepoName(nickname):
            return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.NICKNAME_ALREADY_TAKEN)
        sociallinks = []
        for key in request.POST.keys():
            if str(key).startswith('sociallink'):
                sociallinks.append(request.POST[key])
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
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{freeProjectCreated.__name__}",projectobj)
        alerted = True
        return redirect(projectobj.getLink(success=Message.FREE_PROJECT_CREATED))
    except Exception as e:
        errorLog(e)
        if projectobj and not alerted:
            projectobj.delete()
        return respondRedirect(APPNAME, URL.Projects.CREATE_FREE, error=Message.SUBMISSION_ERROR)

@normal_profile_required
@require_POST
def submitProject(request: WSGIRequest) -> HttpResponse:
    projectobj = None
    try:
        acceptedTerms = request.POST.get("acceptterms", False)
        if not acceptedTerms:
            return respondRedirect(APPNAME, URL.projects.createMod(step=3), error=Message.TERMS_UNACCEPTED)
        license = request.POST.get('license', None)
        if not license:
            return respondRedirect(APPNAME, URL.projects.createMod(step=3), error=Message.LICENSE_UNSELECTED)
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        category = request.POST["projectcategory"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["description"]
        referURL = request.POST.get("referurl", "")
        if not uniqueRepoName(reponame):
            return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.SUBMISSION_ERROR)
        projectobj = createProject(creator=request.user.profile, name=name,
                                   category=category, reponame=reponame, description=description, url=referURL, licenseID=license)
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
        mod = requestModerationForObject(
            projectobj, APPNAME, userRequest, referURL)
        if not mod:
            projectobj.delete()
            return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.SUBMISSION_ERROR)
        addMethodToAsyncQueue(f"{APPNAME}.mailers.{sendProjectSubmissionNotification.__name__}",projectobj)
        return redirect(projectobj.getLink(alert=Message.SENT_FOR_REVIEW))
    except Exception as e:
        errorLog(e)
        if projectobj:
            projectobj.delete()
        return respondRedirect(APPNAME, URL.Projects.CREATE_MOD, error=Message.SUBMISSION_ERROR)


@normal_profile_required
@require_POST
def trashProject(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        project = BaseProject.objects.get(id=projID, creator=request.user.profile)
        project.getProject().moveToTrash()
        return redirect(request.user.profile.getLink(alert=Message.PROJECT_DELETED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
def profileFree(request: WSGIRequest, nickname: str) -> HttpResponse:
    try:
        project = FreeProject.objects.get(nickname=nickname, trashed=False)
        iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
        return renderer(request, Template.Projects.PROFILE_FREE, dict(project=project, iscreator=iscreator))
    except Exception as e:
        raise Http404(e)

@require_GET
def profileMod(request: WSGIRequest, reponame: str) -> HttpResponse:
    try:
        project = Project.objects.get(reponame=reponame, trashed=False)
        if project.status == Code.APPROVED:
            iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
            ismoderator = False if not request.user.is_authenticated else project.getModerator(
            ) == request.user.profile
            return renderer(request, Template.Projects.PROFILE_MOD, dict(project=project, iscreator=iscreator, ismoderator=ismoderator))
        else:
            if request.user.is_authenticated:
                mod = Moderation.objects.filter(project=project, type=APPNAME, status__in=[
                    Code.REJECTED, Code.MODERATION], resolved=False).order_by('-respondOn').first()
                if project.creator == request.user.profile or mod.moderator == request.user.profile:
                    return redirect(mod.getLink(alert=Message.UNDER_MODERATION))
            raise Exception()
    except Exception as e:
        return profileFree(request, reponame)
        # raise Http404(e)


@normal_profile_required
@require_POST
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    try:
        project = BaseProject.objects.get(
            id=projectID, creator=request.user.profile)
        project = project.getProject(True)
        if not project: raise Exception(f'{projectID} project not found')
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
                print(e)
                return redirect(project.getLink(error=Message.ERROR_OCCURRED), permanent=True)
        return redirect(project.getLink(error=Message.ERROR_OCCURRED), permanent=True)
    except Exception as e:
        errorLog(e)
        return HttpResponseForbidden()


@normal_profile_required
@require_JSON_body
def topicsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)

        project = BaseProject.objects.get(id=projID, creator=request.user.profile)
        project = project.getProject(True)
        if not project: raise Exception(f'{projID} project not found')
        excluding = []
        if project:
            for topic in project.getTopics():
                excluding.append(topic.id)

        topics = Topic.objects.exclude(id__in=excluding).filter(
            Q(name__startswith=query.capitalize()) | Q(name__iexact=query))[0:5]
        topicslist = []
        for topic in topics:
            topicslist.append(dict(
                id=topic.getID(),
                name=topic.name
            ))

        return respondJson(Code.OK, dict(
            topics=topicslist
        ))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)



@normal_profile_required
@require_POST
def topicsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        project = BaseProject.objects.get(id=projID,creator=request.user.profile)
        project = project.getProject(True)
        if not project: raise Exception(f'{projID} project not found')
        if not addtopicIDs and not removetopicIDs and not (addtopicIDs.strip() or removetopicIDs.strip()):
            return redirect(project.getLink())
        if removetopicIDs:
            removetopicIDs = removetopicIDs.strip(',').split(',')
            ProjectTopic.objects.filter(
                project=project, topic__id__in=removetopicIDs).delete()

        if addtopicIDs:
            addtopicIDs = addtopicIDs.strip(',').split(',')
            if len(addtopicIDs) < 1:
                return redirect(project.getLink())
            projtops = ProjectTopic.objects.filter(project=project)
            currentcount = projtops.count()
            if currentcount + len(addtopicIDs) > 5:
                return redirect(project.getLink(error=Message.MAX_TOPICS_ACHEIVED))
            for topic in Topic.objects.filter(id__in=addtopicIDs):
                project.topics.add(topic)
                for tag in project.getTags:
                    topic.tags.add(tag)

        return redirect(project.getLink(success=Message.TOPICS_UPDATED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_JSON_body
def tagsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)
        project = BaseProject.objects.get(id=projID,creator=request.user.profile)
        project = project.getProject(True)
        if not project: raise Exception(f'{projID} project not found')
        excludeIDs = []
        if project:
            for tag in project.tags.all():
                excludeIDs.append(tag.id)

        tags = Tag.objects.exclude(id__in=excludeIDs).filter(
            Q(name__startswith=query.lower()) | Q(name__iexact=query))[0:5]
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
def tagsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        removetagIDs = request.POST.get('removetagIDs', None)
        project = BaseProject.objects.get(id=projID, creator=request.user.profile)
        project = project.getProject(True)
        if not project: raise Exception(f'{projID} project not found')
        if not addtagIDs and not removetagIDs and not (addtagIDs.strip() or removetagIDs.strip()):
            return redirect(project.getLink())

        if removetagIDs:
            removetagIDs = removetagIDs.strip(',').split(',')
            ProjectTag.objects.filter(
                project=project, tag__id__in=removetagIDs).delete()

        if addtagIDs:
            addtagIDs = addtagIDs.strip(',').split(',')
            if len(addtagIDs) < 1:
                return redirect(project.getLink())
            projtags = ProjectTag.objects.filter(project=project)
            currentcount = projtags.count()
            if currentcount + len(addtagIDs) > 5:
                return redirect(project.getLink(error=Message.MAX_TAGS_ACHEIVED))
            for tag in Tag.objects.filter(id__in=addtagIDs):
                project.tags.add(tag)
                for topic in project.getTopics():
                    topic.tags.add(tag)

        return redirect(project.getLink(success=Message.TAGS_UPDATED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_JSON_body
def liveData(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        data = cache.get(f"json_livedata_{projID}")
        if not data:
            contributors,languages = getProjectLiveData(project)
            contributorsHTML=renderString(request, Template.Projects.PROFILE_CONTRIBS, dict(contributors=contributors),APPNAME)
            data = dict(
                languages=languages,
                contributorsHTML=str(contributorsHTML),
            )
            cache.set(f"project_livedata_json_{projID}", data, settings.CACHE_SHORT)
        return respondJson(Code.OK, data)
    except Exception as e:
        print(e)
        raise Http404()


# # SHA secret won't allow this hook.
# @csrf_exempt
# @github_only
# def githubEventsListenerFree(request:WSGIRequest,type: str, projID:UUID) -> HttpResponse:
#     if type != Code.HOOK:
#         return HttpResponseBadRequest('Invaild link type')
#     event = request.POST['ghevent']
#     if event != Event.PUSH:
#         HttpResponse('Unsupported event')
#     reponame = request.POST["repository"]["name"]
#     owner_ghID = request.POST["repository"]["owner"]["login"]
#     pusher = request.POST['pusher']
#     try:
#         project = FreeProject.objects.get(id=projID,repolinked=True,nickname=reponame)
#         if owner_ghID != project.creator.ghID:
#             return HttpResponseBadRequest('Invalid owner')
#     except Exception as e:
#         errorLog(f"HOOK: {e}")
#         return HttpResponse(Code.NO)
#     committer = Profile.objects.filter(Q(Q(githubID=pusher['name']) | Q(user__email=pusher['email'])),is_active=True,to_be_zombie=False).first()
#     if committer:
#         committer.increaseXP(by=2)
#         project.creator.increaseXP(by=2)
#     return HttpResponse(Code.OK)

@csrf_exempt
@github_only
def githubEventsListener(request:WSGIRequest, type: str, event: str, projID: UUID) -> HttpResponse:
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Invaild link type')
        ghevent = request.POST['ghevent']
        if ghevent != event:
            return HttpResponseBadRequest('Event mismatch')
        reponame = request.POST["repository"]["name"]
        owner_ghID = request.POST["repository"]["owner"]["login"]
        hookID = request.POST['hookID']
        try:
            project = Project.objects.get(id=projID,reponame=reponame)
            if owner_ghID != PUBNAME:
                return HttpResponseBadRequest('Invalid owner')
        except Exception as e:
            errorLog(f"HOOK: {e}")
            return HttpResponse(Code.NO)
        hookrecord,_ = ProjectHookRecord.objects.get_or_create(hookID=hookID, defaults=dict(
            success=False,
            project=project,
        ))
        if hookrecord.success:
            return HttpResponse(Code.NO)
        if event == Event.PUSH:
            pusher = request.POST['pusher']
            committer = Profile.objects.filter(Q(Q(githubID=pusher['name']) | Q(user__email=pusher['email'])),is_active=True,to_be_zombie=False).first()
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
                    pr_creator = Profile.objects.filter(githubID=pr_creator_ghID, is_active=True).first()
                    if pr_creator:
                        pr_creator.increaseXP(by=5)
                elif action == 'closed':
                    pr_creator = Profile.objects.filter(githubID=pr_creator_ghID, is_active=True).first()
                    if pr['merged']:
                        if pr_creator:
                            pr_creator.increaseXP(by=10)
                        project.creator.increaseXP(by=5)
                        project.moderator.increaseXP(by=5)
                    else:
                        if pr_creator:
                            pr_creator.decreaseXP(by=2)
                elif action == 'reopened':
                    pr_creator = Profile.objects.filter(githubID=pr_creator_ghID, is_active=True).first()
                    if pr_creator:
                        pr_creator.increaseXP(by=2)
                elif action == 'review_requested':
                    pr_reviewer = Profile.objects.filter(githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if pr_reviewer:
                        pr_reviewer.increaseXP(by=5)
                elif action == 'review_request_removed':
                    pr_reviewer = Profile.objects.filter(githubID=pr['requested_reviewer']['login'], is_active=True).first()
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

@require_GET
def browseSearch(request:WSGIRequest):
    query = request.GET.get('query','')
    projects = Project.objects.exclude(trashed=True).filter(Q(
        Q(status=Code.APPROVED), 
        Q(name__startswith=query)
        | Q(name__iexact=query)
        | Q(reponame__startswith=query)
        | Q(reponame__iexact=query)
        | Q(creator__user__first_name__startswith=query)
        | Q(creator__githubID__startswith=query)
        | Q(creator__githubID__iexact=query)
    ))[0:10]
    projects = chain(projects,FreeProject.objects.exclude(trashed=True).filter(Q(
        Q(name__startswith=query)
        | Q(name__iexact=query)
        | Q(nickname__startswith=query)
        | Q(nickname__iexact=query)
        | Q(creator__user__first_name__startswith=query)
        | Q(creator__githubID__startswith=query)
        | Q(creator__githubID__iexact=query)
    ))[0:10])
    return rendererstr(request,Template.Projects.BROWSE_SEARCH,dict(projects=projects, query=query))
