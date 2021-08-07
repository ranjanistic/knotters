from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.auth.decorators import login_required
from django.db.models.query_utils import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from main.decorators import require_JSON_body, github_only
from main.methods import base64ToImageFile, errorLog, respondJson, respondRedirect
from main.strings import Code, Event, Message, URL
from moderation.models import Moderation
from moderation.methods import requestModerationForObject
from people.decorators import profile_active_required
from people.models import Profile, Topic
from .models import License, Project, ProjectTag, ProjectTopic, Tag, Category
from .methods import renderer, rendererstr, uniqueRepoName, createProject, getProjectLiveData
from .apps import APPNAME
from .mailers import sendProjectSubmissionNotification


@require_GET
def allProjects(request: WSGIRequest) -> HttpResponse:
    projects = Project.objects.filter(status=Code.APPROVED)
    return renderer(request, 'index', dict(projects=projects))


@require_GET
def allLicences(request: WSGIRequest) -> HttpResponse:
    try:
        alllicenses = License.objects.filter()
        public = alllicenses.filter(public=True)
        custom = []
        if request.user.is_authenticated:
            custom = alllicenses.filter(
                public=False, creator=request.user.profile)
        return renderer(request, 'license/index', dict(licenses=public, custom=custom))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
def licence(request: WSGIRequest, id: UUID) -> HttpResponse:
    try:
        license = License.objects.get(id=id)
        return renderer(request, 'license/license', dict(license=license))
    except:
        raise Http404()


@require_GET
@profile_active_required
def create(request: WSGIRequest) -> HttpResponse:
    tags = []
    for topic in request.user.profile.getTopics():
        if topic.tags.count():
            tags.append(topic.tags.all()[0])

    if len(tags) < 1:
        tags = list(Tag.objects.all()[0:5])
    if len(tags) < 5:
        tags.append(Tag.objects.all()[0:5-len(tags)])

    categories = Category.objects.all()

    projects = Project.objects.filter(creator=request.user.profile)
    licIDs = []
    if len(projects) > 0:
        for project in projects:
            licIDs.append(project.license.id)

    licenses = License.objects.filter(Q(id__in=licIDs) | Q(public=True))[0:5]

    return renderer(request, 'create', dict(tags=tags, categories=categories, licenses=licenses))


@login_required
@require_JSON_body
def validateField(request: WSGIRequest, field: str) -> JsonResponse:
    try:
        data = request.POST[field]
        if field == 'reponame':
            if not uniqueRepoName(data):
                return respondJson(Code.NO, error=f"{data} already taken, try another.")
            else:
                return respondJson(Code.OK)
        else:
            return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_JSON_body
@login_required
def licences(request: WSGIRequest) -> JsonResponse:
    licenses = License.objects.filter(
        ~Q(id__in=request.POST.get('givenlicenses', []))).values()
    return respondJson(Code.OK, {"licenses": list(licenses)})


@require_JSON_body
@login_required
def addLicense(request: WSGIRequest) -> JsonResponse:
    name = request.POST.get('name', None)
    description = request.POST.get('description', None)
    content = request.POST.get('content', None)
    public = request.POST.get('public', False)

    if not (name and description and content):
        return respondJson(Code.NO, error='Invalid license data')

    if License.objects.filter(name__iexact=str(name).strip()).count() > 0:
        return respondJson(Code.NO, error=f'{name} already exists')
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


@require_POST
@profile_active_required
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


@require_POST
@login_required
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
            return renderer(request, 'profile', dict(project=project, iscreator=iscreator, ismoderator=ismoderator))
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


@require_POST
@login_required
@profile_active_required
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    try:
        project = Project.objects.get(
            id=projectID, creator=request.user.profile)
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
    except Exception as e:
        errorLog(e)
        return HttpResponseForbidden()


@require_JSON_body
@login_required
def topicsSearch(request: WSGIRequest, projID: UUID) -> JsonResponse:
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


@require_POST
@profile_active_required
def topicsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        if not (addtopicIDs.strip() or removetopicIDs.strip()):
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
        errorLog(e)
        raise Http404()


@require_JSON_body
@login_required
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


@require_POST
@profile_active_required
def tagsUpdate(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        removetagIDs = request.POST.get('removetagIDs', None)
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        if not (addtagIDs.strip() or removetagIDs.strip()):
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
def liveData(request: WSGIRequest, projID: UUID) -> HttpResponse:
    try:
        project = Project.objects.get(id=projID, status=Code.APPROVED)
        return rendererstr(request, 'profile/contributors', data=getProjectLiveData(project))
    except:
        raise Http404()


@require_POST
@github_only
def githubEventsListener(request, type: str, event: str, projID: UUID) -> HttpResponse:
    try:
        ghevent = request.META.get('HTTP_X_GITHUB_EVENT', Event.PING)
        if type != Code.HOOK:
            return HttpResponseForbidden('Invaild event type')
        if ghevent == Event.PING:
            return HttpResponse(Code.OK)

        if ghevent != event:
            return HttpResponseForbidden('Event mismatch')
        try:
            project = Project.objects.get(id=projID)
        except Exception as e:
            errorLog(f"HOOK: {e}")
            return HttpResponse(Code.NO)

        if event == Event.PUSH:
            pusher = request.POST.get('pusher')
            committer = Profile.objects.filter(
                Q(Q(githubID=pusher['name']) | Q(user__email=pusher['email']))).first()
            if committer:
                committer.increaseXP(by=2)
            project.creator.increaseXP(by=1)
            project.moderator.increaseXP(by=1)

        return HttpResponse(Code.OK)
    except:
        return Http404()
