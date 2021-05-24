from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from main.renderer import renderView
from .models import *
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
    # user = User.objects.get(id=request.user.id)
    data = {'step':1, 'totalsteps':3 }
    try:
        # step 3 submit
        projectabout = str(request.POST['projectabout']).strip()
        tags = str(request.POST['tags']).strip().split(',')
        projectname = str(request.POST['projectname']).strip()
        reponame = str(request.POST['reponame']).strip()
        nextstep = int(request.POST['nextstep'])
        data["projectabout"] = projectabout
        data["tags"] = str(request.POST['tags']).strip()
        data["projectname"] = projectname
        data["reponame"] = reponame
        if nextstep != 4:
            raise Exception()
        else:
            project = createProject(projectname,reponame,projectabout,tags,None)
            if not project:
                data['step'] = 3
                data['errorfinal'] = 'An error occurred while creating your project.'
                return renderView(request,'project/create.html', data)
            else:
                return redirect(f"/projects/profile/{project.id}")
    except:
        try:
            # step 2 submit
            projectabout = str(request.POST['projectabout']).strip()
            tags = str(request.POST['tags']).strip()
            data["projectabout"] = projectabout
            data["tags"] = tags
            projectname = str(request.POST['projectname']).strip()
            reponame = str(request.POST['reponame']).strip()
            data["projectname"] = projectname
            data["reponame"] = reponame
            data['step'] = 2
            if projectabout == "":
                data['errorprojectabout'] = "Please write something about what this is going to be."
            elif tags == "":
                data['errortags'] = "Assign atleast one keyword relevant to your project."
            else:
                data['step'] = int(request.POST['nextstep'])
            return renderView(request,'project/create.html', data)
        except:
            try:
                # step 1 submit
                projectname = str(request.POST['projectname']).strip()
                reponame = str(request.POST['reponame']).strip()
                data["projectname"] = projectname
                data["reponame"] = reponame
                if projectname == "":
                    data['errorprojectname'] = "Project display name is required"
                elif not uniqueRepoName(reponame):
                    data['errorreponame'] = f"{reponame} already exists"
                else:
                    data['step'] = int(request.POST['nextstep'])
                    projectabout = request.POST['projectabout']
                    tags = request.POST['tags']
                    data["projectabout"] = projectabout
                    data["tags"] = tags
            except:
                pass
        return renderView(request,'project/create.html', data)


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
    return False
    try:
        project = Project.objects.create(creator=user,name=name,reponame=reponame,description=description)
        for tag in tags:
            tag = str(tag).strip().replace(" ","_")
            if uniqueTag(tag):
                tagobj = Tag.objects.create(name=tag)
            else:
                tagobj = Tag.objects.get(name=tag)
            project.tags.add(tagobj)

        g = Github(GITHUBBOTTOKEN)
        org = g.get_organization(PUBNAME)
        repo = org.create_repo(name,private=False,description=description, auto_init=True)
        return project
    except:
        return False
