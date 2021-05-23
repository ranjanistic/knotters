from django.http.response import Http404, HttpResponse
from django.shortcuts import render
from .renderer import renderView
from django.contrib.auth.decorators import login_required
from project.models import Project

def index(request):
    projects = Project.objects.all()
    return renderView(request, 'index.html', {
        "projects":projects
    })

def redirector(request):
    try:
        next = request.GET['n']
    except:
        next = '/'
    if str(next).strip()=='' or next == None:
        next = '/'
    return HttpResponse(f"<h1>Redirecting...</h1><script>window.location.replace('{next}')</script>")

def docIndex(request):
    return renderView(request,"docs/index.html")

def docs(request,type):
    try:
        return renderView(request,f"docs/{type}.html")
    except:
        raise Http404()
