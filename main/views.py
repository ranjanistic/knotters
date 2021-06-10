from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET
from django.shortcuts import redirect
from .methods import renderView
from project.models import Project
from compete.models import Competition
from .strings import code

@require_GET
def index(request):
    projects = Project.objects.filter(status=code.LIVE)[0:3]
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

@require_GET
def redirector(request):
    try:
        next = request.GET['n']
    except:
        next = '/'
    if str(next).strip()=='' or next == None:
        next = '/'

    if next.startswith("http"):
        return HttpResponse(f"<h1>Forwarding...</h1><script>window.location.replace('{next}')</script>")
    else: return redirect(next)

@require_GET
def docIndex(request):
    return renderView(request,"docs/index.html")

@require_GET
def docs(request,type):
    try:
        return renderView(request,f"docs/{type}.html")
    except:
        raise Http404()
