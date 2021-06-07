from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from main.renderer import renderView
from .models import *
from .methods import *
from moderation.views import requestModeration


@require_GET
def allProjects(request):
    projects = Project.objects.all()
    return renderView(request,'project/all.html',{"projects":projects})

@require_GET
def profile(request,reponame):
    project = Project.objects.get(reponame=reponame)
    return renderView(request,'project/profile.html',{"project":project})


@login_required
def create(request):
    return renderView(request,'project/create.html')

@login_required
def submitProject(request):
    try:
        name = request.POST["projectname"]
        description = request.POST["projectabout"]
        reponame = request.POST["reponame"]
        userRequest = request.POST["requestdata"]
        tags = str(request.POST["tags"]).strip().split(",")
        if not uniqueRepoName(reponame):
            return HttpResponse(f'{reponame} already exists')
        projectobj = createProject(name,reponame,description,tags,request.user)
        try:
            image = request.FILES["projectimage"]
            projectobj.image = image
            projectobj.save()
        except:
            pass
        requestModeration(projectobj.id,"project",userRequest)
        return redirect(f'/projects/profile/{projectobj.reponame}')
    except:
        return Http404()

@require_POST
def projectInfo(request, projectID, info):
    try:
        if info == "contributors":
            project = Project.objects.get(id=projectID)
            return HttpResponse(info)
        else: raise Http404()
    except: raise Http404()
