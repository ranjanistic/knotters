from uuid import UUID
from django.views.decorators.csrf import csrf_exempt
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect
from django.conf import settings
from django.views.decorators.cache import cache_page
from main.decorators import require_JSON_body, github_only, normal_profile_required
from main.methods import base64ToImageFile, errorLog, respondJson, respondRedirect
from main.strings import Code, Event, Message, URL, Template
from moderation.models import Moderation
from moderation.methods import requestModerationForObject
from people.models import Profile, Topic
from .models import License, Project, ProjectTag, ProjectTopic, Tag, Category
from .mailers import sendProjectSubmissionNotification
from .methods import renderer, rendererstr, uniqueRepoName, createProject, getProjectLiveData
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
    tags = []
    for topic in request.user.profile.getTopics():
        if topic.tags.count():
            tags.append(topic.tags.all()[0])

    if len(tags) < 5:
        for tag in Tag.objects.all()[0:5-len(tags)]:
            tags.append(tag)

    categories = Category.objects.all()

    projects = Project.objects.filter(creator=request.user.profile)
    licIDs = []
    if len(projects) > 0:
        for project in projects:
            licIDs.append(project.license.id)

    licenses = License.objects.filter(Q(id__in=licIDs) | Q(public=True))[0:5]

    return renderer(request, Template.Projects.CREATE, dict(tags=tags, categories=categories, licenses=licenses))


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

    if License.objects.filter(name__iexact=str(name).strip()).count() > 0:
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
def submitProject(request: WSGIRequest) -> HttpResponse:
    projectobj = None
    try:
        acceptedTerms = request.POST.get("acceptterms", False)
        if not acceptedTerms:
            return respondRedirect(APPNAME, URL.projects.create(step=3), error=Message.TERMS_UNACCEPTED)
        license = request.POST.get('license', None)
        if not license:
            return respondRedirect(APPNAME, URL.projects.create(step=3), error=Message.LICENSE_UNSELECTED)
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        category = request.POST["projectcategory"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["description"]
        referURL = request.POST.get("referurl", "")
        tags = str(request.POST["tags"]).strip().split(",")
        if not uniqueRepoName(reponame):
            return respondRedirect(APPNAME, URL.Projects.CREATE, error=Message.SUBMISSION_ERROR)
        projectobj = createProject(creator=request.user.profile, name=name,
                                   category=category, reponame=reponame, description=description, tags=tags, url=referURL, licenseID=license)
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
            return respondRedirect(APPNAME, URL.Projects.CREATE, error=Message.SUBMISSION_ERROR)
        sendProjectSubmissionNotification(projectobj)
        return redirect(projectobj.getLink(alert=Message.SENT_FOR_REVIEW))
    except Exception as e:
        errorLog(e)
        if projectobj:
            projectobj.delete()
        return respondRedirect(APPNAME, URL.Projects.CREATE, error=Message.SUBMISSION_ERROR)


@normal_profile_required
@require_POST
def trashProject(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        project = Project.objects.get(
            id=projID, creator=request.user.profile, status=Code.REJECTED, trashed=False)
        project.moveToTrash()
        return redirect(request.user.profile.getLink(alert=Message.PROJECT_DELETED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
def profile(request: WSGIRequest, reponame: str) -> HttpResponse:
    try:
        project = Project.objects.get(reponame=reponame, trashed=False)
        if project.status == Code.APPROVED:
            iscreator = False if not request.user.is_authenticated else project.creator == request.user.profile
            ismoderator = False if not request.user.is_authenticated else project.getModerator(
            ) == request.user.profile
            return renderer(request, Template.Projects.PROFILE, dict(project=project, iscreator=iscreator, ismoderator=ismoderator))
        else:
            if request.user.is_authenticated:
                mod = Moderation.objects.filter(project=project, type=APPNAME, status__in=[
                    Code.REJECTED, Code.MODERATION], resolved=False).order_by('-respondOn').first()
                if project.creator == request.user.profile or mod.moderator == request.user.profile:
                    return redirect(mod.getLink(alert=Message.UNDER_MODERATION))
            raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    try:
        project = Project.objects.get(
            id=projectID, creator=request.user.profile,status=Code.APPROVED)
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
                return redirect(project.getLink(), permanent=True)
            except:
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

        project = Project.objects.filter(id=projID, status=Code.APPROVED).first()
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
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        if not addtopicIDs and not removetopicIDs and not (addtopicIDs.strip() or removetopicIDs.strip()):
            return redirect(project.getLink())

        if removetopicIDs:
            removetopicIDs = removetopicIDs.strip(',').split(',')
            ProjectTopic.objects.filter(
                project=project, topic__id__in=removetopicIDs).delete()

        if addtopicIDs:
            addtopicIDs = addtopicIDs.strip(',').split(',')
            projtops = ProjectTopic.objects.filter(project=project)
            currentcount = projtops.count()
            if currentcount + len(addtopicIDs) > 5:
                return redirect(project.getLink())

            for topic in Topic.objects.filter(id__in=addtopicIDs):
                project.topics.add(topic)

        return redirect(project.getLink())
    except Exception as e:
        print(e)
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_JSON_body
def tagsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)
        project = Project.objects.filter(
            id=projID, status=Code.APPROVED).first()
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
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        if not addtagIDs and not removetagIDs and not (addtagIDs.strip() or removetagIDs.strip()):
            return redirect(project.getLink())

        if removetagIDs:
            removetagIDs = removetagIDs.strip(',').split(',')
            ProjectTag.objects.filter(
                project=project, tag__id__in=removetagIDs).delete()

        if addtagIDs:
            addtagIDs = addtagIDs.strip(',').split(',')
            projtags = ProjectTag.objects.filter(project=project)
            currentcount = projtags.count()
            if currentcount + len(addtagIDs) > 5:
                return redirect(project.getLink())

            for tag in Tag.objects.filter(id__in=addtagIDs):
                project.tags.add(tag)

        return redirect(project.getLink())
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
@cache_page(settings.CACHE_SHORT)
def liveData(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        return rendererstr(request, Template.Projects.PROFILE_CONTRIBS, data=getProjectLiveData(project))
    except Exception as e:
        print(e)
        raise Http404()


@csrf_exempt
@github_only
def githubEventsListener(request, type: str, event: str, projID: UUID) -> HttpResponse:
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Invaild event type')
        ghevent = request.POST['ghevent']
        if ghevent != event:
            return HttpResponseBadRequest('Event mismatch')
        try:
            project = Project.objects.get(id=projID)
        except Exception as e:
            errorLog(f"HOOK: {e}")
            return HttpResponse(Code.NO)

        if event == Event.PUSH:
            pusher = request.POST.get('pusher', {'email': '', 'name': ''})
            committer = Profile.objects.filter(Q(Q(githubID=pusher['name']) | Q(user__email=pusher['email'])),is_active=True).first()
            if committer:
                committer.increaseXP(by=2)
                project.creator.increaseXP(by=2)
                project.moderator.increaseXP(by=2)
        elif event == Event.PR:
            pr = request.POST.get('pull_request', None)
            if pr:
                action = request.POST.get('action', None)
                creator_ghID = pr['user']['login']
                if action == 'opened':
                    creator = Profile.objects.filter(githubID=creator_ghID, is_active=True).first()
                    if creator:
                        creator.increaseXP(by=5)
                elif action == 'closed':
                    creator = Profile.objects.filter(githubID=creator_ghID, is_active=True).first()
                    if pr['merged']:
                        if creator:
                            creator.increaseXP(by=10)
                        project.creator.increaseXP(by=5)
                        project.moderator.increaseXP(by=5)
                    else:
                        if creator:
                            creator.decreaseXP(by=2)
                elif action == 'reopened':
                    creator = Profile.objects.filter(githubID=creator_ghID, is_active=True).first()
                    if creator:
                        creator.increaseXP(by=2)
                elif action == 'review_requested':
                    reviewer = Profile.objects.filter(githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if reviewer:
                        reviewer.increaseXP(by=5)
                elif action == 'review_request_removed':
                    reviewer = Profile.objects.filter(githubID=pr['requested_reviewer']['login'], is_active=True).first()
                    if reviewer:
                        reviewer.decreaseXP(by=5)
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
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404()
