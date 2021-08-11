from uuid import UUID
from django.http.response import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from allauth.account.decorators import verified_email_required, login_required
from django.views.decorators.http import require_GET, require_POST
from main.decorators import require_JSON_body, normal_profile_required
from main.methods import base64ToImageFile, errorLog, respondJson, renderData
from main.env import MAILUSER
from main.strings import Action, Code, Message
from .apps import APPNAME
from .models import ProfileSetting, ProfileTopic, Topic, User, Profile
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML, convertToFLname, filterBio, migrateUserAssets, rendererstr, profileString
from .mailers import successorInvite, accountReactiveAlert, accountInactiveAlert


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    people = Profile.objects.filter(~Q(Q(is_zombie=True) | Q(to_be_zombie=True)), is_active=True, suspended=False)
    data = dict(people=people)
    return renderer(request, 'index', data)


@require_GET
def profile(request: WSGIRequest, userID: UUID or str) -> HttpResponse:
    try:
        if request.user.is_authenticated:
            if request.user.profile.to_be_zombie or request.user.profile.is_zombie:
                raise Exception()
            if request.user.profile.githubID == userID:
                return renderer(request, 'profile', dict(person=request.user))
            if request.user.id == UUID(userID):
                if not request.user.githubID:
                    return renderer(request, 'profile', dict(person=request.user))
                return redirect(request.user.getLink())
            profile = Profile.objects.get(Q(Q(githubID=userID)|Q(user__id=userID)), is_zombie=False, to_be_zombie=False, is_active=True,suspended=False)
            return renderer(request, 'profile', dict(person=profile.user))
    except:
        print('her')
        pass
    try:
        user = User.objects.get(id=userID)
        if not user.profile.isNormal():
            raise Exception()
        if user.profile.githubID:
            return redirect(user.profile.getLink())
        return renderer(request, 'profile', dict(person=user))
    except:
        print(2)
        pass
    try:
        profile = Profile.objects.get(githubID=userID)
        if not profile.isNormal():
            raise Exception()
        return renderer(request, 'profile', dict(person=profile.user))
    except:
        raise Http404()


@require_GET
def profileTab(request: WSGIRequest, userID: UUID, section: str) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.id == userID:
            profile = request.user.profile
        else:
            profile = Profile.objects.get(user__id=userID)
        return getProfileSectionHTML(profile, section, request)
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
@normal_profile_required
def settingTab(request: WSGIRequest, section: str) -> HttpResponse:
    try:
        data = getSettingSectionHTML(request.user, section, request)
        if data:
            return data
        else:
            raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_POST
@verified_email_required
@normal_profile_required
def editProfile(request: WSGIRequest, section: str) -> HttpResponse:
    try:
        profile = Profile.objects.get(user=request.user)
        if section == 'pallete':
            userchanged = False
            profilechanged = False
            try:
                base64Data = str(request.POST['profilepic'])
                imageFile = base64ToImageFile(base64Data)
                if imageFile:
                    profile.picture = imageFile
                    profilechanged = True
            except:
                pass
            try:
                fname, lname = convertToFLname(
                    str(request.POST['displayname']))
                bio = str(request.POST['profilebio']).strip()
                if fname != profile.user.first_name:
                    profile.user.first_name = fname
                    userchanged = True
                if lname != profile.user.last_name:
                    profile.user.last_name = lname
                    userchanged = True
                if filterBio(bio) != profile.bio:
                    profile.bio = filterBio(bio)
                    profilechanged = True
                
                if userchanged:
                    profile.user.save()
                if profilechanged:
                    profile.save()
                return redirect(profile.getLink())
            except:
                return redirect(profile.getLink(error=Message.ERROR_OCCURRED))
        else: raise Exception()
    except:
        return HttpResponseForbidden()


@require_POST
@verified_email_required
def accountprefs(request: WSGIRequest, userID: UUID) -> HttpResponse:
    try:
        if str(request.user.getID()) != str(userID):
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
        return redirect(request.user.profile.getLink(alert=Message.ACCOUNT_PREF_SAVED))
    except Exception as e:
        errorLog(e)
        return redirect(request.user.profile.getLink(error=Message.ERROR_OCCURRED))

@require_JSON_body
def topicsSearch(request:WSGIRequest)->JsonResponse:
    query = request.POST.get('query',None)
    if not query:
        return respondJson(Code.NO)
    excluding = []
    if request.user.is_authenticated:
        for topic in request.user.profile.getTopics():
            excluding.append(topic.id)

    topics = Topic.objects.exclude(id__in=excluding).filter(Q(name__startswith=query.capitalize())|Q(name__iexact=query))[0:5]
    topicslist = []
    for topic in topics:
        topicslist.append(dict(
            id=topic.getID(),
            name=topic.name
        ))
    
    return respondJson(Code.OK,dict(
        topics=topicslist
    ))

@require_POST
@normal_profile_required
def topicsUpdate(request:WSGIRequest) -> HttpResponse:
    try:
        addtopicIDs = request.POST.get('addtopicIDs',None)
        removetopicIDs = request.POST.get('removetopicIDs',None)
        if not (addtopicIDs.strip() or removetopicIDs.strip()):
            return redirect(request.user.profile.getLink())

        if removetopicIDs:
            removetopicIDs = removetopicIDs.strip(',').split(',')
            ProfileTopic.objects.filter(profile=request.user.profile,topic__id__in=removetopicIDs).update(trashed=True)

        if addtopicIDs:
            addtopicIDs = addtopicIDs.strip(',').split(',')
            proftops = ProfileTopic.objects.filter(profile=request.user.profile)
            currentcount = proftops.filter(trashed=False).count()
            if currentcount + len(addtopicIDs) > 5:
                return redirect(request.user.profile.getLink(error=Message.ERROR_OCCURRED))

            newcount = currentcount + len(addtopicIDs)
            proftops.filter(topic__id__in=addtopicIDs).update(trashed=False)
            if request.user.profile.totalTopics() != newcount:
                for topic in Topic.objects.filter(id__in=addtopicIDs):
                    request.user.profile.topics.add(topic)

        return redirect(request.user.profile.getLink())
    except Exception as e:
        errorLog(e)
        raise Http404()
        

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
            return respondJson(Code.NO)
        if activate and not request.user.profile.is_active:
            is_active = True
        elif deactivate and request.user.profile.is_active:
            is_active = False
        else:
            return respondJson(Code.NO)
        done = Profile.objects.filter(
            user=request.user).update(is_active=is_active)
        if not done:
            return respondJson(Code.NO)
        if is_active:
            accountReactiveAlert(request.user.profile)
        else:
            accountInactiveAlert(request.user.profile)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_JSON_body
@normal_profile_required
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
            return respondJson(Code.NO)
        successor = None
        if set:
            if userID and request.user.email != userID:
                try:
                    successor = User.objects.get(email=userID)
                    if not successor.profile.githubID:
                        return respondJson(Code.NO, error=Message.SUCCESSOR_GH_UNLINKED)
                    if successor.profile.successor == request.user:
                        if not successor.profile.successor_confirmed:
                            successorInvite(request.user, successor)
                        return respondJson(Code.NO, error=Message.SUCCESSOR_OF_PROFILE)
                    successor_confirmed = False
                except:
                    return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
            elif usedefault == True or userID == MAILUSER:
                try:
                    successor = User.objects.get(email=MAILUSER)
                    successor_confirmed = True
                except Exception as e:
                    print(e)
                    return respondJson(Code.NO)
            else:
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        elif unset and request.user.profile.successor:
            successor = None
            successor_confirmed = False
        else:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)

        Profile.objects.filter(user=request.user).update(
            successor=successor, successor_confirmed=successor_confirmed)
        if successor and not successor_confirmed:
            successorInvite(successor=successor, predecessor=request.user)
        return respondJson(Code.OK)
    except Exception as e:
        print(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_JSON_body
@normal_profile_required
def getSuccessor(request: WSGIRequest) -> JsonResponse:
    if request.user.profile.successor:
        return respondJson(Code.OK, dict(
            successorID=(request.user.profile.successor.email if request.user.profile.successor.email != MAILUSER else '')
        ))
    return respondJson(Code.NO)


@require_GET
@normal_profile_required
def successorInvitation(request: WSGIRequest, predID: UUID) -> HttpResponse:
    """
    Render profile successor invitation view.
    """
    try:
        predecessor = User.objects.get(id=predID)
        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise Exception()
        return render(request, "invitation.html", renderData(dict(predecessor=predecessor), APPNAME))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_POST
@verified_email_required
def successorInviteAction(request: WSGIRequest, action: str) -> HttpResponse:
    """
    Sets the successor if accepted, or sets default successor.
    Also deletes the predecessor account and migrates assets, only if it was scheduled to be deleted.
    """
    predID = request.POST.get('predID', None)
    accept = action == Action.ACCEPT

    try:
        if True and (not accept and action != Action.DECLINE) or not predID or predID == request.user.getID():
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

        alert = Message.SUCCESSORSHIP_DECLINED
        if accept:
            alert = Message.SUCCESSORSHIP_ACCEPTED
        profile = Profile.objects.get(id=predecessor.profile.id)
        return redirect(profile.getLink(alert=alert))
    except:
        return HttpResponseForbidden()


@require_JSON_body
@normal_profile_required
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
        return respondJson(Code.NO)
    if not request.user.profile.successor:
        return respondJson(Code.NO, error=Message.SUCCESSOR_UNSET)
    try:
        done = Profile.objects.filter(
            user=request.user).update(to_be_zombie=True)
        User.objects.filter(id=request.user.id).update(is_active=False)
        if request.user.profile.successor_confirmed:
            user = User.objects.get(id=request.user.id)
            migrateUserAssets(user, user.profile.successor)
            user.delete()
        return respondJson(Code.OK if done else Code.NO, message=Message.ACCOUNT_DELETED)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@normal_profile_required
def zombieProfile(request: WSGIRequest, profileID: UUID) -> HttpResponse:
    try:
        profile = Profile.objects.get(
            id=profileID, successor=request.user, successor_confirmed=True)
        profile.picture = str(profile.picture)
        return respondJson(Code.OK, model_to_dict(profile))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
def newbieProfiles(request:WSGIRequest) -> HttpResponse:
    excludeIDs = []
    if request.user.is_authenticated:
        excludeIDs.append(request.user.profile.getID())
    profiles = Profile.objects.exclude(id__in=excludeIDs).filter(suspended=False,is_zombie=False,to_be_zombie=False,is_active=True).order_by('-createdOn')[0:10]
    return rendererstr(request,'browse/newbie', dict(profiles=profiles))
