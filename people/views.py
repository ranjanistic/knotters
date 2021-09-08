from uuid import UUID
from django.views.decorators.csrf import csrf_exempt
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from django.conf import settings
from django.views.decorators.cache import cache_page
from allauth.account.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from main.decorators import github_only, require_JSON_body, normal_profile_required
from main.methods import base64ToImageFile, errorLog, respondJson, renderData
from main.env import BOTMAIL
from main.strings import Action, Code, Event, Message, Template
from .apps import APPNAME
from .models import ProfileSetting, ProfileTopic, Topic, User, Profile
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML, convertToFLname, filterBio, migrateUserAssets, rendererstr, profileString
from .mailers import successorInvite, accountReactiveAlert, accountInactiveAlert


@require_GET
# @cache_page(settings.CACHE_LONG)
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.People.INDEX)


@require_GET
def profile(request: WSGIRequest, userID: UUID or str) -> HttpResponse:
    try:
        self = False
        if request.user.is_authenticated and (request.user.getID() == userID or request.user.profile.githubID == userID):
            person = request.user
            self = True
        else:
            try:
                person = User.objects.get(
                    id=userID, profile__to_be_zombie=False, profile__suspended=False)
                if person.profile.ghID:
                    return redirect(person.profile.getLink())
            except:
                try:
                    profile = Profile.objects.get(
                        githubID=userID, to_be_zombie=False, suspended=False)
                    person = profile.user
                except:
                    raise Exception()
        if request.user.is_authenticated:
            if person.profile.isBlocked(request.user):
                raise Exception()
        return renderer(request, Template.People.PROFILE, dict(person=person, self=self))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
def profileTab(request: WSGIRequest, userID: UUID, section: str) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.id == userID:
            profile = request.user.profile
        else:
            profile = Profile.objects.get(user__id=userID)
        if request.user.is_authenticated:
            if profile.isBlocked(request.user):
                raise Exception()
        data = getProfileSectionHTML(profile, section, request)
        print(data)
        return data
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_GET
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


@normal_profile_required
@require_POST
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
        else:
            raise Exception()
    except:
        return HttpResponseForbidden()


@normal_profile_required
@require_POST
def accountprefs(request: WSGIRequest) -> HttpResponse:
    try:
        newsletter = str(request.POST.get('newsletter', 'off')) != 'off'
        recommendations = str(request.POST.get(
            'recommendations', 'off')) != 'off'
        competitions = str(request.POST.get('competitions', 'off')) != 'off'
        privatemail = str(request.POST.get('privatemail', 'off')) != 'off'
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
def topicsSearch(request: WSGIRequest) -> JsonResponse:
    query = request.POST.get('query', None)
    if not query:
        return respondJson(Code.NO)
    excluding = []
    if request.user.is_authenticated:
        for topic in request.user.profile.getTopics():
            excluding.append(topic.id)

    topics = Topic.objects.exclude(id__in=excluding).filter(
        Q(name__startswith=query.capitalize()) | Q(name__iexact=query))[0:5]
    topicslist = []
    for topic in topics:
        topicslist.append(dict(
            id=topic.getID(),
            name=topic.name
        ))

    return respondJson(Code.OK, dict(
        topics=topicslist
    ))


@normal_profile_required
@require_POST
def topicsUpdate(request: WSGIRequest) -> HttpResponse:
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        if not addtopicIDs and not removetopicIDs and not (addtopicIDs.strip() or removetopicIDs.strip()):
            return redirect(request.user.profile.getLink())

        if removetopicIDs:
            removetopicIDs = removetopicIDs.strip(',').split(',')
            ProfileTopic.objects.filter(
                profile=request.user.profile, topic__id__in=removetopicIDs).update(trashed=True)

        if addtopicIDs:
            addtopicIDs = addtopicIDs.strip(',').split(',')
            proftops = ProfileTopic.objects.filter(
                profile=request.user.profile)
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


@login_required
@require_JSON_body
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
        if is_active and request.user.profile.suspended:
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


@normal_profile_required
@require_JSON_body
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
            if usedefault or userID == BOTMAIL:
                try:
                    successor = User.objects.get(email=BOTMAIL)
                    successor_confirmed = True
                except Exception as e:
                    errorLog(e)
                    return respondJson(Code.NO)
            elif userID and request.user.email != userID:
                try:
                    successor = User.objects.get(email=userID)
                    if successor.profile.isBlocked(request.user):
                        return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
                    if not successor.profile.ghID and not successor.profile.githubID:
                        return respondJson(Code.NO, error=Message.SUCCESSOR_GH_UNLINKED)
                    if successor.profile.successor == request.user:
                        if not successor.profile.successor_confirmed:
                            successorInvite(request.user, successor)
                        return respondJson(Code.NO, error=Message.SUCCESSOR_OF_PROFILE)
                    successor_confirmed = userID == BOTMAIL
                except:
                    return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
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
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON_body
def getSuccessor(request: WSGIRequest) -> JsonResponse:
    if request.user.profile.successor:
        return respondJson(Code.OK, dict(
            successorID=(
                request.user.profile.successor.email if request.user.profile.successor.email != BOTMAIL else '')
        ))
    return respondJson(Code.NO)


@normal_profile_required
@require_GET
def successorInvitation(request: WSGIRequest, predID: UUID) -> HttpResponse:
    """
    Render profile successor invitation view.
    """
    try:
        predecessor = User.objects.get(id=predID)
        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise Exception()
        return render(request, Template().invitation, renderData(dict(predecessor=predecessor), APPNAME))
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def successorInviteAction(request: WSGIRequest, action: str) -> HttpResponse:
    """
    Sets the successor if accepted, or sets default successor.
    Also deletes the predecessor account and migrates assets, only if it was scheduled to be deleted.
    """
    predID = request.POST.get('predID', None)
    accept = action == Action.ACCEPT

    try:
        if (not accept and action != Action.DECLINE) or not predID or predID == request.user.getID():
            raise Exception()

        predecessor = User.objects.get(id=predID)

        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise Exception()

        if not accept:
            if predecessor.profile.to_be_zombie:
                successor = User.objects.get(email=BOTMAIL)
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


@normal_profile_required
@require_JSON_body
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

@normal_profile_required
@require_JSON_body
def blockUser(request: WSGIRequest):
    try:
        userID = request.POST['userID']
        user = User.objects.get(id=userID)
        request.user.profile.blockUser(user)
        return respondJson(Code.OK)
    except Exception as e:
        return respondJson(Code.NO)

@normal_profile_required
@require_JSON_body
def unblockUser(request: WSGIRequest):
    try:
        userID = request.POST['userID']
        user = User.objects.get(id=userID)
        request.user.profile.unblockUser(user)
        return respondJson(Code.OK)
    except Exception as e:
        print(e)
        return respondJson(Code.NO)

@csrf_exempt
@github_only
def githubEventsListener(request, type: str, event: str) -> HttpResponse:
    try:
        if type != Code.HOOK:
            return HttpResponseBadRequest('Invaild event type')
        ghevent = request.POST['ghevent']
        if event != ghevent:
            return HttpResponseBadRequest(f'event mismatch')

        action = request.POST.get('action', None)
        if ghevent == Event.ORG:
            if action == Event.MEMBER_ADDED:
                membership = request.POST.get('membership', None)
                if membership:
                    member = Profile.objects.filter(
                        githubID=membership['user']['login'], is_active=True).first()
                    if member:
                        member.increaseXP(by=10)
            elif action == Event.MEMBER_REMOVED:
                membership = request.POST.get('membership', None)
                if membership:
                    member = Profile.objects.filter(
                        githubID=membership['user']['login']).first()
                    # if member:
                    #     member.decreaseXP(by=10)
        elif ghevent == Event.TEAMS:
            if action == Event.CREATED:
                team = request.POST.get('team', None)
                if team:
                    team['name']
        else:
            return HttpResponseBadRequest(ghevent)
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT: {e}")
        raise Http404()
