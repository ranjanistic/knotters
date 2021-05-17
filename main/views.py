from django.http.response import HttpResponse
from .renderer import renderView
from django.contrib.auth.decorators import login_required
from project.models import Project

def index(request):
    projects = Project.objects.all()
    return renderView(request, 'index.html', {
        "projects":projects
    })

def redirector(request):
    next = request.GET['n']

    if str(next).strip()=='' or next == None:
        next = '/'
    return HttpResponse(f"<h1>Redirecting...</h1><script>window.location.replace('{next}')</script>")
