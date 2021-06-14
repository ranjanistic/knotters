from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from .models import *
from .methods import *
from moderation.methods import requestModeration
from main.strings import code
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


@login_required
def create(request):
    tags = Tag.objects.all()[0:5]
    categories = Category.objects.all()
    return renderer(request, 'create.html', {
        "tags":tags,
        "categories":categories
    })

@login_required
@require_POST
def submitProject(request):
    try:
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["requestdata"]
        tags = str(request.POST["tags"]).strip().split(",")
        if not uniqueRepoName(reponame):
            return HttpResponse(f'{reponame} already exists')
        projectobj = createProject(
            name, reponame, description, tags, request.user)
        try:
            image = request.FILES["projectimage"]
            projectobj.image = image
            projectobj.save()
        except:
            pass
        mod = requestModeration(projectobj.id, APPNAME, userRequest)
        if not mod:
            return HttpResponse(code.NO)
        return redirect(f'/projects/profile/{projectobj.reponame}')
    except:
        return HttpResponse(code.NO)


@require_POST
def projectInfo(request, projectID, info):
    try:
        if info == "contributors":
            project = Project.objects.get(id=projectID,status=code.LIVE)
            return HttpResponse(info)
        else:
            raise Http404()
    except:
        raise Http404()
