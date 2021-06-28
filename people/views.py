from django.http.response import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from allauth.account.decorators import verified_email_required, login_required
from django.views.decorators.http import require_GET, require_POST
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML
from .models import User, Profile
from main.methods import base64ToImageFile
from .methods import convertToFLname, filterBio


@require_GET
def index(request):
    users = User.objects.filter(is_active=True)
    return renderer(request, 'index', {"people": users})


@require_GET
def profile(request, userID):
    if request.user.is_authenticated and (request.user.id == userID or request.user.profile.githubID == userID):
        return renderer(request, 'profile', {"person": request.user})
    else:
        try:
            profile = Profile.objects.get(githubID=userID)
            return renderer(request, 'profile', {"person": profile.user})
        except:
            pass
        try:
            user = User.objects.get(id=userID)
            if user.profile.githubID:
                return redirect(user.profile.getLink())
            return renderer(request, 'profile', {"person": user})
        except:
            raise Http404()


@require_GET
def profileTab(request, userID, section):
    try:
        if request.user.is_authenticated and request.user.id == userID:
            user = request.user
        else:
            user = User.objects.get(id=userID)
        data = getProfileSectionHTML(user.profile, section, request)
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
        data = getSettingSectionHTML(request.user, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Http404()
    except Exception as e:
        raise Http404()


@require_POST
@verified_email_required
def editProfile(request, section):
    try:
        profile = Profile.objects.get(user=request.user)
        if section == 'pallete':
            try:
                base64Data = str(request.POST['profilepic'])
                imageFile = base64ToImageFile(base64Data)
                if imageFile:
                    profile.picture = imageFile
            except:
                pass
            try:
                fname, lname = convertToFLname(str(request.POST['displayname']))
                bio = str(request.POST['profilebio'])
                profile.user.first_name = fname
                profile.user.last_name = lname
                profile.user.save()
                profile.bio = filterBio(bio)
                profile.save()
                return redirect(profile.getLink(success=f"Pallete updated"), permanent=True)
            except:
                return redirect(profile.getLink(error=f"Problem occurred."))
    except:
        raise HttpResponseForbidden()

@require_POST
@login_required
def accountsettings(request,userID):
    try:
        if request.user.id != userID: raise Exception()
        newemail = str(request.POST['newemail']).strip().lower()
        oldpassword = request.POST['oldpassword']
        newpassword = request.POST['newpassword']
        return redirect(request.user.profile.getLink(alert="Account info saved."))
    except:
        return redirect(request.user.profile.getLink(error="Invalid info provided"))

@require_POST
@login_required
def accountprefs(request,userID):
    try:
        if request.user.id != userID: raise Exception()
        newemail = str(request.POST['newemail']).strip().lower()
        oldpassword = request.POST['oldpassword']
        newpassword = request.POST['newpassword']
        return redirect(request.user.profile.getLink(alert="Account preferences saved."))
    except:
        return redirect(request.user.profile.getLink(error="Invalid preferences provided"))