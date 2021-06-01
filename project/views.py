from django.contrib.auth.decorators import login_required
from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from main.renderer import renderView
from .models import *
from people.models import User
from main.env import GITHUBBOTTOKEN, PUBNAME
from github import Github

def allProjects(request):
    projects = Project.objects.all()
    return renderView(request,'project/all.html',{"projects":projects})

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
        return redirect(f'/projects/profile/{projectobj.reponame}')
    except:
        return Http404()

def uniqueRepoName(reponame):
    try:
        Project.objects.get(reponame=reponame)
    except:
        return True
    return False

def uniqueTag(tagname):
    try:
        Tag.objects.get(name=tagname)
    except:
        return True
    return False


# Creates project on knotters & then repository in github/Knotters using knottersbot
def createProject(name,reponame,description,tags,user):
    try:
        project = Project.objects.create(creator=user,name=name,reponame=reponame,description=description)
        for tag in tags:
            tag = str(tag).strip().replace(" ","_")
            if uniqueTag(tag):
                tagobj = Tag.objects.create(name=tag)
            else:
                tagobj = Tag.objects.get(name=tag)
            project.tags.add(tagobj)
        return project
    except:
        return False

def createRepository(reponame,description):
    return False
    g = Github(GITHUBBOTTOKEN)
    org = g.get_organization(PUBNAME)
    repo = org.create_repo(name=reponame,private=False,description=description, auto_init=True)
    return repo

def protectBranchMain():
    return None