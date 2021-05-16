from django.http.response import Http404, HttpResponse
from main.renderer import renderView
from .models import Project

def allProjects(request):
    projects = Project.objects.all()
    return renderView(request,'project/all.html',{"projects":projects})

def profile(request,id):
    project = Project.objects.get(id=id)
    return renderView(request,'project/profile.html',{"project":project})