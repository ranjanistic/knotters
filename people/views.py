from django.http.response import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.views.decorators.http import require_GET, require_POST
from .methods import renderer, getProfileSectionHTML,getSettingSectionHTML
from django.contrib.auth.decorators import login_required
from .models import User, Profile
from .apps import APPNAME
from main.strings import code

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
        data = getProfileSectionHTML(user,section,request)
        if data:
            return HttpResponse(data)
        else:
            raise Http404()
    except:
        raise Http404()

@require_GET
@login_required
def settingTab(request, section):
    try:
        data = getSettingSectionHTML(request.user,section,request)
        if data:
            return HttpResponse(data)
        else:
            raise Http404()
    except:
        raise Http404()

@login_required
@require_POST
def editProfile(request,section):
    try:
        user = User.objects.get(id=request.user.id)
        if section == 'pallete':
            try:
                image = request.FILES["profilepic"]
                user.image = image
            except: pass
            try:
                name = str(request.POST['displayname']).split(" ")
                fname = name[0]
                del name[0]
                if len(name) > 1:
                    lname = "".join(name)
                elif len(name) == 1:
                    lname = name
                else: lname = None

                user.first_name = fname
                user.last_name = lname
            except: pass
            try:
                bio = str(request.POST['bio'])
                user.profile.bio = bio
            except: pass
            user.save()
        return redirect(user.profile.getLink())
    except:
        raise HttpResponseForbidden()
