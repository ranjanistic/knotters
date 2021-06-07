from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from main.renderer import renderView
from django.contrib.auth.decorators import login_required
from project.models import Project
from .models import User

@require_GET
def index(request):
    return renderView(request, 'people/index.html')

@require_GET
def profile(request, userID):
    user = User.objects.get(id=userID)
    return renderView(request, 'people/profile.html', {"person": user})

@require_POST
def userInfo(request, userID, section):
    try:
        user = User.objects.get(id=userID)
        if section == 'overview':
            return HttpResponse("Overview")
        elif section == 'projects':
            projects = Project.objects.filter(creator=user)
            return HttpResponse(projects)
        elif section == 'contribution':
            return HttpResponse("Contribution")
        elif section == 'activity':
            return HttpResponse("Activity")
        else:
            raise Http404()
    except:
        raise Http404()
