from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from .methods import renderer, getProfileSectionHTML
from django.contrib.auth.decorators import login_required
from project.models import Project
from .models import User


@require_GET
def index(request):
    users = User.objects.filter(is_active=True,is_verified=True)
    return renderer(request, 'index.html', {"people": users})


@require_GET
def profile(request, userID):
    user = User.objects.get(id=userID)
    projects = Project.objects.filter(creator=user)
    return renderer(request, 'profile.html', {"person": user,"project":projects,"contribution":"","overview":"","activity":""})

@require_GET
def profileTab(request, userID, section):
    try:
        if request.user.is_authenticated and request.user.id == userID:
            user = request.user
        else:
            user = User.objects.get(id=userID)
        data = getProfileSectionHTML(user,section)
        if data:
            return HttpResponse(data)
        else:
            raise Http404()
    except:
        raise Http404()
