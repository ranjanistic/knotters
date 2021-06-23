from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import redirect
from .methods import renderView
from projects.models import Project
from compete.models import Competition
from .strings import code, PROJECTS, COMPETE, PEOPLE

@require_GET
def offline(request):
    return renderView(request, 'offline')

@require_GET
def index(request):
    projects = Project.objects.filter(status=code.LIVE)[0:3]
    data = {
        "projects": projects
    }
    try:
        comp = Competition.objects.get(active=True)
        data["alert"] = {
            "message": f"The '{comp.title}' competition is on!",
            "url": f"/competitions/{comp.id}"
        }
    except:
        pass
    return renderView(request, 'index', data)


@require_GET
def redirector(request):
    next = request.GET.get('n', '/')
    next = '/' if str(next).strip() == '' or not next else next
    return redirect(next) if next.startswith("/") else HttpResponse(f"<h1>Redirecting to {next}</h1><script>window.location.replace('{next}')</script>")


@require_GET
def docIndex(request):
    return renderView(request, "index", fromApp='docs')


@require_GET
def docs(request, type):
    try:
        return renderView(request, type, fromApp='docs')
    except:
        raise Http404()


@require_GET
def landing(request):
    parts = request.build_absolute_uri().split('/')
    try:
        subapp = parts[len(parts)-2]
        if not [PEOPLE, PROJECTS, COMPETE].__contains__(subapp):
            subapp = ''
        return renderView(request, "landing", fromApp=subapp)
    except:
        raise Http404()
