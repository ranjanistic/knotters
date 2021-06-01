from django.http.response import Http404, HttpResponse
from .renderer import renderView
from project.models import Project
from compete.models import Competition

def index(request):
    projects = Project.objects.filter()[0:3]
    data = {
        "projects":projects
    }
    try:
        comp = Competition.objects.get(active=True)
        data["alert"] = {
            "message": f"The '{comp.title}' competition is on!",
            "url": f"/competitions/{comp.id}"
        }
    except:
        pass
    return renderView(request, 'index.html', data)

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
