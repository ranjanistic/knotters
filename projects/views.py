from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from main.decorators import require_JSON_body
from main.methods import base64ToImageFile
from main.strings import code
from moderation.methods import requestModeration
from .models import *
from .methods import *
from .apps import APPNAME


@require_GET
def allProjects(request):
    projects = Project.objects.filter(status=code.MODERATION)
    return renderer(request, 'index.html', {"projects": projects})


@require_GET
def profile(request, reponame):
    try:
        project = Project.objects.get(reponame=reponame)
        if project.status == code.LIVE:
            return renderer(request, 'profile.html', {"project": project})
        if request.user.is_authenticated and project.creator == request.user:
            if project.status == code.REJECTED:
                return redirect(f'/moderation/{APPNAME}/{project.id}')
            if project.status == code.MODERATION:
                return renderer(request, 'profile.html', {"project": project})
        raise Http404()
    except:
        raise Http404()


@require_POST
@login_required
def editProfile(request, projectID, section):
    try:
        changed = False
        project = Project.objects.get(id=projectID)
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
                return redirect(project.getLink(success=f"Pallete updated"), permanent=True)
            except:
                return redirect(project.getLink(error=f"Problem occurred."))
    except:
        raise HttpResponseForbidden()


@require_GET
@login_required
def create(request):
    tags = Tag.objects.all()[0:5]
    categories = Category.objects.all()
    return renderer(request, 'create.html', {
        "tags": tags,
        "categories": categories
    })


@require_POST
@login_required
@require_JSON_body
def validateField(request, field):
    try:
        data = request.POST[field]
        if field == 'reponame':
            if not uniqueRepoName(data):
                raise Exception(f"{data} already taken, try another.")
            else:
                pass
        else:
            return Http404()
        return JsonResponse({'code': code.OK})
    except Exception as e:
        return JsonResponse({'error': str(e)})


@require_POST
@login_required
def submitProject(request):
    try:
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["description"]
        tags = str(request.POST["tags"]).strip().split(",")
        if not uniqueRepoName(reponame):
            return HttpResponse(f'{reponame} already exists')
        projectobj = createProject(
            name, reponame, description, tags, request.user)
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
        mod = requestModeration(projectobj.id, APPNAME, userRequest)
        print(mod)
        if not mod:
            return redirect(f"/projects/create?e=Error in submission, try again later 2.")
        return redirect(projectobj.getLink(success="Your project has been submitted for moderation."))
    except Exception as e:
        print(e)
        return redirect(f"/projects/create?e=Error in submission, try again later 1.")


@require_POST
def projectInfo(request, projectID, info):
    try:
        if info == "contributors":
            project = Project.objects.get(id=projectID, status=code.LIVE)
            return HttpResponse(info)
        else:
            raise Http404()
    except:
        raise Http404()
