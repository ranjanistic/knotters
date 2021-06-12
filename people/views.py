from django.http.response import Http404, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST
from .methods import renderer, getProfileSectionHTML
from django.contrib.auth.decorators import login_required
from .models import User, Profile
from .apps import APPNAME

@require_GET
def index(request):
    users = User.objects.filter(is_active=True)
    return renderer(request, 'index.html', {"people": users})


@require_GET
def profile(request, userID):
    try:
        user = User.objects.get(id=userID)
        if user.profile.githubID != None:
            return redirect(f"/{APPNAME}/profile/{user.profile.githubID}")
        return renderer(request, 'profile.html', {"person": user})
    except:
        pass
    try:
        profile = Profile.objects.get(githubID=userID)
        return renderer(request, 'profile.html', {"person": profile.user})
    except:
        raise Http404()

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
