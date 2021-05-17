from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from main.renderer import renderView
from .models import Project

def allProjects(request):
    projects = Project.objects.all()
    return renderView(request,'project/all.html',{"projects":projects})

def profile(request,id):
    project = Project.objects.get(id=id)
    return renderView(request,'project/profile.html',{"project":project})

@login_required
def create(request):
    data = {'step':1, 'totalsteps':3 }
    print(request.POST)
    try:
        # step 3
        projectabout = request.POST['projectabout']
        tags = request.POST['tags']
        projectname = request.POST['projectname']
        reponame = request.POST['reponame']
        nextstep = int(request.POST['nextstep'])
        if nextstep != 4:
            raise Exception()
        else: return redirect('/') # create project
    except:
        try:
            # step 2
            projectabout = request.POST['projectabout']
            tags = request.POST['tags']
            projectname = request.POST['projectname']
            reponame = request.POST['reponame']
            data['step'] = int(request.POST['nextstep'])
            data["projectname"] = projectname
            data["reponame"] = reponame
            data["projectabout"] = projectabout
            data["tags"] = tags
            return renderView(request,'project/create.html', data)
        except:
            try:
                # step 1
                projectname = request.POST['projectname']
                reponame = request.POST['reponame']
                data['step'] = int(request.POST['nextstep'])
                data["projectname"] = projectname
                data["reponame"] = reponame
                projectabout = request.POST['projectabout']
                tags = request.POST['tags']
                data["projectabout"] = projectabout
                data["tags"] = tags
            except:
                pass
        return renderView(request,'project/create.html', data)