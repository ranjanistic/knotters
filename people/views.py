from uuid import UUID
from django.views.decorators.csrf import csrf_exempt
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from allauth.account.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from main.decorators import decode_JSON, github_only, require_JSON_body, normal_profile_required
from main.methods import addMethodToAsyncQueue, base64ToImageFile, errorLog, respondJson, renderData
from main.env import BOTMAIL
from main.strings import Action, Code, Event, Message, Template
from management.models import ReportCategory
from .apps import APPNAME
from .models import ProfileSetting, ProfileTopic, Topic, User, Profile
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML, convertToFLname, filterBio, migrateUserAssets, rendererstr, profileString
from .mailers import successorAccepted, successorDeclined, successorInvite, accountReactiveAlert, accountInactiveAlert


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.People.INDEX)


@require_GET
def profile(request: WSGIRequest, userID: UUID or str) -> HttpResponse:
    try:
        self = False
        if request.user.is_authenticated and (request.user.getID() == userID or request.user.profile.ghID == userID):
            person = request.user
            self = True
        else:
            try:
                person = User.objects.get(
                    id=userID, profile__to_be_zombie=False, profile__suspended=False, profile__is_active=True)
                if person.profile.ghID:
                    return redirect(person.profile.getLink())
            except:
                try:
                    profile = Profile.objects.get(
                        githubID=userID, to_be_zombie=False, suspended=False, is_active=True)
                    person = profile.user
                except:
                    raise Exception()
            if request.user.is_authenticated:
                if person.profile.isBlocked(request.user):
                    raise Exception()
        return renderer(request, Template.People.PROFILE, dict(person=person, self=self))
    except Exception as e:
        raise Http404()


@require_GET
def profileTab(request: WSGIRequest, userID: UUID, section: str) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.id == userID:
            profile = request.user.profile
        else:
            profile = Profile.objects.get(
                user__id=userID)
        if request.user.is_authenticated:
            if profile.isBlocked(request.user):
                raise Exception()
        return getProfileSectionHTML(profile, section, request)
    except Exception as e:
        print(e)
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
        raise Http404()


@normal_profile_required
@require_POST
@decode_JSON
def editProfile(request: WSGIRequest, section: str) -> HttpResponse:
    try:
        profile = Profile.objects.get(user=request.user)
        nextlink = request.POST.get('next', None)
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
                if fname and fname != profile.user.first_name:
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
                    return redirect(nextlink or profile.getLink(success=Message.PROFILE_UPDATED))
                return redirect(nextlink or profile.getLink())
            except Exception as e:
                return redirect(nextlink or profile.getLink(error=Message.ERROR_OCCURRED))
        else:
            raise Exception()
    except Exception as e:
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
    excludeProfileTopics = request.POST.get('excludeProfileTopics', True)
    excludeProfileAllTopics = request.POST.get('excludeProfileAllTopics', False)
    if not query:
        return respondJson(Code.NO)
    excluding = []
    if request.user.is_authenticated:
        if excludeProfileAllTopics:
            excluding = excluding + request.user.profile.getAllTopicIds
        elif excludeProfileTopics:
            excluding = excluding + request.user.profile.getTopicIds
    topics = Topic.objects.exclude(id__in=excluding).filter(
        Q(name__istartswith=query)
        | Q(name__iendswith=query)
        | Q(name__iexact=query)
        | Q(name__icontains=query)
    )[0:5]
    topicslist = []
    for topic in topics:
        topicslist.append(dict(
            id=topic.get_id,
            name=topic.name
        ))

    return respondJson(Code.OK, dict(
        topics=topicslist
    ))


@normal_profile_required
@require_POST
@decode_JSON
def topicsUpdate(request: WSGIRequest) -> HttpResponse:
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        visibleTopicIDs = request.POST.get('visibleTopicIDs', None)
        if not addtopicIDs and not removetopicIDs and not visibleTopicIDs:
            if request.POST.get('JSON_BODY', False):
                return respondJson(Code.NO)
            if not (addtopicIDs.strip() or removetopicIDs.strip()):
                return redirect(request.user.profile.getLink())

        if removetopicIDs:
            if not request.POST.get('JSON_BODY', False):
                removetopicIDs = removetopicIDs.strip(',').split(',')
            ProfileTopic.objects.filter(
                profile=request.user.profile, topic__id__in=removetopicIDs).update(trashed=True)

        if addtopicIDs:
            if not request.POST.get('JSON_BODY', False):
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
        print(visibleTopicIDs)
        if visibleTopicIDs and len(visibleTopicIDs) > 0:
            if len(visibleTopicIDs)>5: return respondJson(Code.NO,error=Message.MAX_TOPICS_ACHEIVED)
            for topic in Topic.objects.filter(id__in=visibleTopicIDs):
                request.user.profile.topics.add(topic)
            ProfileTopic.objects.filter(profile=request.user.profile).exclude(topic__id__in=visibleTopicIDs).update(trashed=True)
            ProfileTopic.objects.filter(profile=request.user.profile,topic__id__in=visibleTopicIDs).update(trashed=False)

        if request.POST.get('JSON_BODY', False):
            return respondJson(Code.OK)
        return redirect(request.user.profile.getLink())
    except Exception as e:
        errorLog(e)
        if request.POST.get('JSON_BODY', False):
            return respondJson(Code.NO,error=Message.ERROR_OCCURRED)
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
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{accountReactiveAlert.__name__}", request.user.profile)
        else:
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{accountInactiveAlert.__name__}", request.user.profile)
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
                    successor = User.objects.get(
                        email=userID)
                    if successor.profile.isBlocked(request.user):
                        return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
                    if not successor.profile.ghID and not successor.profile.githubID:
                        return respondJson(Code.NO, error=Message.SUCCESSOR_GH_UNLINKED)
                    if successor.profile.successor == request.user:
                        if not successor.profile.successor_confirmed:
                            addMethodToAsyncQueue(
                                f"{APPNAME}.mailers.{successorInvite.__name__}", request.user, successor)
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
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{successorInvite.__name__}", successor, request.user)
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

        if accept:
            successor = request.user
            predecessor.profile.successor_confirmed = True
        else:
            if predecessor.profile.to_be_zombie:
                successor = User.objects.get(email=BOTMAIL)
                predecessor.profile.successor_confirmed = True
            else:
                successor = None

        predecessor.profile.successor = successor
        predecessor.profile.save()

        deleted = False
        if predecessor.profile.to_be_zombie:
            migrateUserAssets(predecessor, successor)
            predecessor.delete()
            deleted = True

        if accept:
            alert = Message.SUCCESSORSHIP_ACCEPTED
            if not deleted:
                addMethodToAsyncQueue(
                    f"{APPNAME}.mailers.{successorAccepted.__name__}", successor, predecessor)
        else:
            alert = Message.SUCCESSORSHIP_DECLINED
            if not deleted:
                addMethodToAsyncQueue(
                    f"{APPNAME}.mailers.{successorDeclined.__name__}", request.user, predecessor)
        if not deleted:
            return redirect(predecessor.profile.getLink(alert=alert))
        return redirect(request.user.profile.getLink(alert=alert))
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


def reportCategories(request: WSGIRequest):
    try:
        categories = ReportCategory.objects.filter().order_by("name")
        reports = []
        for cat in categories:
            reports.append(dict(id=cat.id, name=cat.name))
        return respondJson(Code.OK, dict(reports=reports))
    except Exception as e:
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
def reportUser(request: WSGIRequest):
    try:
        report = request.POST['report']
        userID = request.POST['userID']
        user = User.objects.get(id=userID)
        category = ReportCategory.objects.get(id=report)
        request.user.profile.reportUser(user, category)
        return respondJson(Code.OK)
    except Exception as e:
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
def blockUser(request: WSGIRequest):
    try:
        userID = request.POST['userID']
        user = User.objects.get(id=userID)
        request.user.profile.blockUser(user)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
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
        errorLog(e)
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


@require_GET
def browseSearch(request: WSGIRequest):
    query = request.GET.get('query', '')
    excludeIDs = []
    if request.user.is_authenticated:
        excludeIDs = request.user.profile.blockedIDs
    fname, lname = convertToFLname(query)
    profiles = Profile.objects.exclude(user__id__in=excludeIDs).filter(Q(
        Q(is_active=True, suspended=False, to_be_zombie=False),
        Q(user__email__istartswith=query)
        | Q(user__email__icontains=query)
        | Q(user__first_name__istartswith=fname)
        | Q(user__first_name__iendswith=fname)
        | Q(user__last_name__istartswith=(lname or fname))
        | Q(user__last_name__iendswith=(lname or fname))
        | Q(githubID__istartswith=query)
        | Q(githubID__iexact=query)
        | Q(user__first_name__iexact=query)
        | Q(user__last_name__iexact=query)
        | Q(user__last_name__iexact=(lname or fname))
    ))[0:20]
    return rendererstr(request, Template.People.BROWSE_SEARCH, dict(profiles=profiles, query=query))
