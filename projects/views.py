from inspect import currentframe, getframeinfo
from django.core.handlers.wsgi import WSGIRequest
from uuid import UUID
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseForbidden
from moderation.models import Moderation
from django.shortcuts import redirect
from main.decorators import require_JSON_body
from main.methods import base64ToImageFile, respondJson
from main.strings import code
from moderation.methods import requestModerationForObject
from people.decorators import profile_active_required
from .models import Project, Tag, Category
from .methods import renderer, uniqueRepoName, createProject
from .apps import APPNAME
from .mailers import sendProjectSubmissionNotification


@require_GET
def allProjects(request: WSGIRequest) -> HttpResponse:
    projects = Project.objects.filter(status=code.MODERATION)
    return renderer(request, 'index', {"projects": projects})


@require_GET
@profile_active_required
def create(request: WSGIRequest) -> HttpResponse:
    tags = Tag.objects.all()[0:5]
    categories = Category.objects.all()
    return renderer(request, 'create', {
        "tags": tags,
        "categories": categories
    })


@login_required
@require_JSON_body
def validateField(request: WSGIRequest, field: str) -> JsonResponse:
    try:
        data = request.POST[field]
        if field == 'reponame':
            if not uniqueRepoName(data):
                return respondJson(code.NO, error=f"{data} already taken, try another.")
            else:
                return respondJson(code.OK)
        else:
            return respondJson(code.NO)
    except Exception as e:
        print(e)
        return respondJson(code.NO, error="An error occurred")


@require_POST
@login_required
@profile_active_required
def submitProject(request: WSGIRequest) -> HttpResponse:
    projectobj = None
    try:
        acceptedTerms = request.POST.get("acceptterms", False)
        if not acceptedTerms:
            return redirect(f"/{APPNAME}/create?e=You have not accepted the terms.")
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        category = request.POST["projectcategory"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["description"]
        referURL = request.POST.get("referurl", "")
        tags = str(request.POST["tags"]).strip().split(",")
        if not uniqueRepoName(reponame):
            return HttpResponse(f'{reponame} already exists')
        projectobj = createProject(creator=request.user.profile, name=name,
                category=category, reponame=reponame, description=description, tags=tags, url=referURL)
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
            return redirect(f"/{APPNAME}/create?e=Error in submission, try again later 1.")
        sendProjectSubmissionNotification(projectobj)
        return redirect(projectobj.getLink(alert="Sent for review"))
    except Exception as e:
        if projectobj:
            projectobj.delete()
        return redirect(f"/{APPNAME}/create?e=Error in submission, try again later.")

@require_POST
@login_required
def trashProject(request:WSGIRequest, projID:UUID) -> HttpResponse:
    try:
        Project.objects.filter(id=projID,creator=request.user.profile,status=code.REJECTED).delete()
        return redirect(request.user.profile.getLink(alert="Project deleted"))
    except:
        raise Http404()

@require_GET
@profile_active_required
def profile(request: WSGIRequest, reponame: str) -> HttpResponse:
    try:
        project = Project.objects.get(reponame=reponame)
        if project.status == code.APPROVED:
            return renderer(request, 'profile', {"project": project})
        else:
            mod = Moderation.objects.filter(project=project, type=APPNAME, status__in=[
                                            code.REJECTED, code.MODERATION]).order_by('-respondOn')[0]
            if request.user.is_authenticated and (project.creator == request.user.profile or mod.moderator == request.user.profile):
                return redirect(mod.getLink())
            raise Exception()
    except Exception as e:
        print(e)
        raise Http404()


@require_POST
@login_required
@profile_active_required
def editProfile(request: WSGIRequest, projectID: UUID, section: str) -> HttpResponse:
    try:
        changed = False
        project = Project.objects.get(
            id=projectID, creator=request.user.profile)
        if section == 'pallete':
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
                return redirect(project.getLink(error=f"Problem occurred."), permanent=True)
    except:
        return HttpResponseForbidden()
