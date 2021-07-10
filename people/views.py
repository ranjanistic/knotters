from uuid import UUID
from django.http.response import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from allauth.account.decorators import verified_email_required, login_required
from django.views.decorators.http import require_GET, require_POST
from main.decorators import require_JSON_body
from main.methods import base64ToImageFile, respondJson, renderData
from main.env import MAILUSER
from main.strings import code
from .apps import APPNAME
from .decorators import profile_active_required
from .models import ProfileSetting, User, Profile
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML, convertToFLname, filterBio, migrateUserAssets
from .mailers import successorInvite, accountReactiveAlert, accountInactiveAlert


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    people = Profile.objects.filter(
        is_active=True, is_zombie=False, to_be_zombie=False, suspended=False)
    return renderer(request, 'index', {"people": people})


@require_GET
def profile(request: WSGIRequest, userID: UUID or str) -> HttpResponse:
    try:
        if request.user.is_authenticated:
            if request.user.profile.to_be_zombie or request.user.profile.is_zombie:
                raise Http404()
            if request.user.profile.githubID == userID:
                return renderer(request, 'profile', {"person": request.user})
            if request.user.id == UUID(userID):
                return renderer(request, 'profile', {"person": request.user})
            profile = Profile.objects.get(
                githubID=userID, is_zombie=False, to_be_zombie=False, is_active=True)
            return renderer(request, 'profile', {"person": profile.user})
    except:
        pass
    try:
        user = User.objects.get(id=userID)
        if user.profile.to_be_zombie or user.profile.is_zombie or not user.profile.is_active:
            raise Exception()
        if user.profile.githubID:
            return redirect(user.profile.getLink())
        return renderer(request, 'profile', {"person": user})
    except:
        pass
    try:
        profile = Profile.objects.get(githubID=userID)
        if profile.to_be_zombie or profile.is_zombie or not profile.is_active:
            raise Exception()
        return renderer(request, 'profile', {"person": profile.user})
    except:
        raise Http404()


@require_GET
def profileTab(request: WSGIRequest, userID: UUID, section: str) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.id == userID:
            user = request.user
        else:
            user = User.objects.get(id=userID)
        data = getProfileSectionHTML(user.profile, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
    except Exception as e:
        print(e)
        raise Http404()


@require_GET
@login_required
@profile_active_required
def settingTab(request: WSGIRequest, section: str) -> HttpResponse:
    try:
        data = getSettingSectionHTML(request.user, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
    except Exception as e:
        raise Http404()


@require_POST
@verified_email_required
@profile_active_required
def editProfile(request: WSGIRequest, section: str) -> HttpResponse:
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
                fname, lname = convertToFLname(
                    str(request.POST['displayname']))
                bio = str(request.POST['profilebio'])
                profile.user.first_name = fname
                profile.user.last_name = lname
                profile.user.save()
                profile.bio = filterBio(bio)
                profile.save()
                return redirect(profile.getLink())
            except:
                return redirect(profile.getLink(error=f"Problem occurred."))
    except:
        raise HttpResponseForbidden()


@require_POST
@verified_email_required
def accountprefs(request: WSGIRequest, userID: UUID) -> HttpResponse:
    try:
        if str(request.user.id) != str(userID):
            raise Exception()
        newsletter = True if str(request.POST.get(
            'newsletter', 'off')) != 'off' else False
        recommendations = True if str(request.POST.get(
            'recommendations', 'off')) != 'off' else False
        competitions = True if str(request.POST.get(
            'competitions', 'off')) != 'off' else False
        privatemail = True if str(request.POST.get(
            'privatemail', 'off')) != 'off' else False
        ProfileSetting.objects.filter(profile=request.user.profile).update(
            newsletter=newsletter,
            recommendations=recommendations,
            competitions=competitions,
            privatemail=privatemail
        )
        return redirect(request.user.profile.getLink(alert="Account preferences saved."))
    except Exception as e:
        print(e)
        return redirect(request.user.profile.getLink(error="An error occurred"))


@require_JSON_body
@login_required
def accountActivation(request: WSGIRequest) -> JsonResponse:
    """
    Activate or deactivate account.
    Does not delete anything, just meant to hide profile from the world whenever the requesting user wants.
    """
    activate = request.POST.get('activate', None)
    deactivate = request.POST.get('deactivate', None)
    try:
        if activate == deactivate:
            return respondJson(code.NO)
        if activate and not request.user.profile.is_active:
            is_active = True
        elif deactivate and request.user.profile.is_active:
            is_active = False
        else:
            return respondJson(code.NO)
        done = Profile.objects.filter(
            user=request.user).update(is_active=is_active)
        if is_active:
            accountReactiveAlert(request.user.profile)
        else:
            accountInactiveAlert(request.user.profile)
        return respondJson(code.OK)
    except Exception as e:
        print(e)
        return respondJson(code.NO, error=str(e))


@require_JSON_body
@login_required
def profileSuccessor(request: WSGIRequest):
    """
    To set/modify/unset profile successor. If default is chosen by the requestor, then sets the default successor and successor confirmed as true.
    Otherwise, updates successor and sends invitation email to successor if set, and sets successor confirmed as false,
    which will change only when the invited successor acts on invitation.
    """
    set = request.POST.get('set', None)
    userID = request.POST.get('userID', None)
    usedefault = request.POST.get('useDefault', False)
    unset = request.POST.get('unset', None)

    try:
        if set == unset:
            return respondJson(code.NO)
        successor = None
        if set:
            if userID and request.user.email != userID:
                try:
                    successor = User.objects.get(email=userID)
                    if not successor.profile.githubID:
                        return respondJson(code.NO, error='Your successor should have Github profile linked to their account.')
                    if successor.profile.successor == request.user:
                        if not successor.profile.successor_confirmed:
                            successorInvite(request.user, successor)
                        return respondJson(code.NO, error='You are the successor of this profile.')
                    successor_confirmed = False
                except:
                    return respondJson(code.NO, error='Successor not found')
            elif usedefault == True or userID == MAILUSER:
                try:
                    successor = User.objects.get(email=MAILUSER)
                    successor_confirmed = True
                except Exception as e:
                    print(e)
                    return respondJson(code.NO)
            else:
                return respondJson(code.NO, error="Invalid request")
        elif unset and request.user.profile.successor:
            successor = None
            successor_confirmed = False
        else:
            return respondJson(code.NO, error="Invalid request")

        Profile.objects.filter(user=request.user).update(
            successor=successor, successor_confirmed=successor_confirmed)
        if successor and not successor_confirmed:
            successorInvite(successor=successor, predecessor=request.user)
        return respondJson(code.OK)
    except Exception as e:
        print(e)
        return respondJson(code.NO, error=str(e))


@require_JSON_body
@login_required
def getSuccessor(request: WSGIRequest) -> JsonResponse:
    if request.user.profile.successor:
        return respondJson(code.OK, {
            'successorID': request.user.profile.successor.email if request.user.profile.successor.email != MAILUSER else ''
        })
    return respondJson(code.NO)


@require_GET
@login_required
def successorInvitation(request: WSGIRequest, predID: UUID) -> HttpResponse:
    """
    Render profile successor invitation view.
    """
    try:
        predecessor = User.objects.get(id=predID)
        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise Exception()
        return render(request, "invitation.html", renderData({
            'predecessor': predecessor
        }, APPNAME))
    except Exception as e:
        print(e)
        raise Http404()


@require_POST
@verified_email_required
def successorInviteAction(request: WSGIRequest, action: str) -> HttpResponse:
    """
    Sets the successor if accepted, or sets default successor.
    Also deletes the predecessor account and migrates assets, only if it was scheduled to be deleted.
    """
    predID = request.POST.get('predID', None)
    accept = action == 'accept'

    try:
        if True and (not accept and action != 'decline') or not predID or predID == request.user.getID():
            raise Exception()

        predecessor = User.objects.get(id=predID)

        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise Exception()

        if not accept:
            if predecessor.profile.to_be_zombie:
                successor = User.objects.get(email=MAILUSER)
                predecessor.profile.successor_confirmed = True
            else:
                successor = None
        else:
            successor = request.user
            predecessor.profile.successor_confirmed = True

        predecessor.profile.successor = successor
        predecessor.profile.save()

        if predecessor.profile.to_be_zombie:
            migrateUserAssets(predecessor, successor)
            predecessor.delete()

        alert = "You\'ve declined this profile\'s successorship"
        if accept:
            alert = "You\'re now the successor of this profile\'s assets."
        profile = Profile.objects.get(id=predecessor.profile.id)
        return redirect(profile.getLink(alert=alert))
    except:
        return HttpResponseForbidden()


@require_JSON_body
@login_required
def accountDelete(request: WSGIRequest) -> JsonResponse:
    """
    Account for deletion, only if a successor is set.
    If successor has not been confirmed yet,
    then just schedules account to be deleted at the moment the successor is confirmed.
    Otherwise, deletes the account and makes the profile a zombie.

    For the requesting user, successfull response of this endpoint should imply permanent inaccess to their account,
    regardless of successor confirmation state.
    """
    confirmed = request.POST.get('confirmed', False)
    if not confirmed:
        return respondJson(code.NO)
    if not request.user.profile.successor:
        return respondJson(code.NO, error='Successor not set, use default successor if none.')
    try:
        done = Profile.objects.filter(
            user=request.user).update(to_be_zombie=True)
        message = "Account will be deleted."
        User.objects.filter(id=request.user.id).update(is_active=False)
        if request.user.profile.successor_confirmed:
            user = User.objects.get(id=request.user.id)
            migrateUserAssets(user, user.profile.successor)
            user.delete()
            message = "Account deleted successfully."
        return respondJson(code.OK if done else code.NO, message=message)
    except Exception as e:
        print(e)
        return respondJson(code.NO)


@login_required
def zombieProfile(request: WSGIRequest, profileID: UUID) -> HttpResponse:
    try:
        profile = Profile.objects.get(
            id=profileID, successor=request.user, successor_confirmed=True)
        profile.picture = str(profile.picture)
        return respondJson(code.OK, model_to_dict(profile))
    except Exception as e:
        print(e)
        raise Http404()
