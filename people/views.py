from uuid import UUID
import re
from django.core.cache import cache
from ratelimit.decorators import ratelimit
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.http.response import Http404, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.forms.models import model_to_dict
from django.shortcuts import redirect, render
from allauth.account.decorators import login_required
from django.conf import settings
from django.views.decorators.http import require_GET, require_POST
from main.decorators import decode_JSON, github_only, require_JSON_body, normal_profile_required
from main.methods import addMethodToAsyncQueue, base64ToImageFile, errorLog, respondJson, renderData
from main.env import BOTMAIL
from main.strings import Action, Code, Event, Message, Template
from management.models import Management, ReportCategory
from .apps import APPNAME
from .models import ProfileSetting, ProfileSocial, ProfileTopic, Topic, User, Profile
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML, convertToFLname, filterBio, migrateUserAssets, rendererstr, profileString
from .mailers import successorAccepted, successorDeclined, successorInvite, accountReactiveAlert, accountInactiveAlert


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.People.INDEX)


@require_GET
def profile(request: WSGIRequest, userID: UUID or str) -> HttpResponse:
    try:
        self = False
        if request.user.is_authenticated and (request.user.getID() == userID or request.user.profile.ghID() == userID):
            person = request.user
            self = True
        else:
            try:
                person = User.objects.get(
                    id=userID, profile__to_be_zombie=False, profile__suspended=False, profile__is_active=True)
                if person.profile.has_ghID():
                    return redirect(person.profile.getLink())
            except:
                try:
                    profile = Profile.objects.get(
                        githubID=userID, to_be_zombie=False, suspended=False, is_active=True)
                    person = profile.user
                except:
                    raise ObjectDoesNotExist()
            if request.user.is_authenticated:
                if person.profile.isBlocked(request.user):
                    raise ObjectDoesNotExist()
        gh_orgID = None
        has_ghID = person.profile.has_ghID()
        if has_ghID:
            gh_orgID = person.profile.gh_orgID()
        is_manager = person.profile.is_manager()
        is_admirer = False
        if request.user.is_authenticated:
            is_admirer = person.profile.admirers.filter(user=request.user).exists()
        return renderer(request, Template.People.PROFILE, dict(person=person, self=self,has_ghID=has_ghID,gh_orgID=gh_orgID,is_manager=is_manager,is_admirer=is_admirer))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


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
                raise ObjectDoesNotExist(profile)
        return getProfileSectionHTML(profile, section, request)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_GET
def settingTab(request: WSGIRequest, section: str) -> HttpResponse:
    try:
        data = getSettingSectionHTML(request.user, section, request)
        if data:
            return data
        else:
            raise Exception(data)
    except Exception as e:
        raise Http404(e)


@normal_profile_required
@require_POST
@decode_JSON
def editProfile(request: WSGIRequest, section: str) -> HttpResponse:
    json_body = request.POST.get(Code.JSON_BODY,False)
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
                    if json_body:
                        return respondJson(Code.OK, message=Message.PROFILE_UPDATED)
                    return redirect(nextlink or profile.getLink(success=Message.PROFILE_UPDATED))
                if json_body:
                    return respondJson(Code.OK)
                return redirect(nextlink or profile.getLink())
            except Exception as e:
                if json_body:
                    return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
                return redirect(nextlink or profile.getLink(error=Message.ERROR_OCCURRED))
        elif section == "sociallinks":
            sociallinks = []
            for key in request.POST.keys():
                if str(key).startswith('sociallink'):
                    link = str(request.POST[key]).strip()
                    if link:
                        sociallinks.append(link)
            sociallinks = list(set(sociallinks))[:5]
            ProfileSocial.objects.filter(profile=request.user.profile).delete()
            if len(sociallinks) > 0:
                profileSocials = []
                for link in sociallinks:
                    profileSocials.append(
                        ProfileSocial(profile=request.user.profile, site=link))
                ProfileSocial.objects.bulk_create(profileSocials)
                if json_body:
                    return respondJson(Code.OK, message=Message.PROFILE_UPDATED)
                return redirect(nextlink or profile.getLink(success=Message.PROFILE_UPDATED))
            else:
                if json_body:
                    return respondJson(Code.OK)
                return redirect(nextlink or profile.getLink())
        else:
            raise ObjectDoesNotExist(section)
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)


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
            excluding = excluding + request.user.profile.getAllTopicIds()
        elif excludeProfileTopics:
            excluding = excluding + request.user.profile.getTopicIds()
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
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        visibleTopicIDs = request.POST.get('visibleTopicIDs', None)
        addtopics = request.POST.get('addtopics', None)
        updated = False
        if not (addtopicIDs or removetopicIDs or visibleTopicIDs or addtopics):
            if json_body:
                return respondJson(Code.NO)
            if not (addtopicIDs.strip() or removetopicIDs.strip()):
                return redirect(request.user.profile.getLink())

        if removetopicIDs:
            if not json_body:
                removetopicIDs = removetopicIDs.strip(',').split(',')
            ProfileTopic.objects.filter(
                profile=request.user.profile, topic__id__in=removetopicIDs).update(trashed=True)
            updated = True

        if addtopicIDs:
            if not json_body:
                addtopicIDs = addtopicIDs.strip(',').split(',')
            proftops = ProfileTopic.objects.filter(
                profile=request.user.profile)
            currentcount = proftops.filter(trashed=False).count()
            if currentcount + len(addtopicIDs) > 5:
                if json_body:
                    return respondJson(Code.NO,error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(request.user.profile.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            newcount = currentcount + len(addtopicIDs)
            proftops.filter(topic__id__in=addtopicIDs).update(trashed=False)
            if request.user.profile.totalTopics() != newcount:
                for topic in Topic.objects.filter(id__in=addtopicIDs):
                    request.user.profile.topics.add(topic)
                updated = True

        if visibleTopicIDs and len(visibleTopicIDs) > 0:
            if len(visibleTopicIDs)>5: return respondJson(Code.NO,error=Message.MAX_TOPICS_ACHEIVED)
            for topic in Topic.objects.filter(id__in=visibleTopicIDs):
                request.user.profile.topics.add(topic)
            ProfileTopic.objects.filter(profile=request.user.profile).exclude(topic__id__in=visibleTopicIDs).update(trashed=True)
            ProfileTopic.objects.filter(profile=request.user.profile,topic__id__in=visibleTopicIDs).update(trashed=False)
            updated = True

        if addtopics and len(addtopics) > 0:
            count = ProfileTopic.objects.filter(profile=request.user.profile,trashed=False).count()
            if not json_body:
                addtopics = addtopics.strip(',').split(',')
            if count + len(addtopics) > 5:
                if json_body:
                    return respondJson(Code.NO,error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(request.user.profile.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            profiletopics = []
            for top in addtopics:
                if len(top) > 35:
                    continue
                top = re.sub('[^a-zA-Z \\\s-]', '', top)
                if len(top) > 35:
                    continue
                topic, _ = Topic.objects.get_or_create(name__iexact=top,defaults=dict(name=str(top).capitalize(),creator=request.user.profile))
                profiletopics.append(ProfileTopic(topic=topic,profile=request.user.profile))
            if len(profiletopics) > 0:
                ProfileTopic.objects.bulk_create(profiletopics)
                updated = True
                
        if updated:
            cache.delete(request.user.profile.CACHE_KEYS.topic_ids)

        if json_body:
            return respondJson(Code.OK)
        return redirect(request.user.profile.getLink())
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO,error=Message.ERROR_OCCURRED)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO,error=Message.ERROR_OCCURRED)
        raise Http404(e)


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
            raise ObjectDoesNotExist()
        if activate and not request.user.profile.is_active:
            is_active = True
        elif deactivate and request.user.profile.is_active:
            is_active = False
        else:
            raise ObjectDoesNotExist()
        if is_active and request.user.profile.suspended:
            raise ObjectDoesNotExist()

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
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
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
            elif userID and request.user.email != userID and not (userID in request.user.emails()):
                try:
                    if request.user.profile.is_manager():
                        smgm = Management.objects.get(profile__user__email=userID)
                        successor = smgm.profile.user
                    else:
                        successor = User.objects.get(
                            email=userID)

                    if successor.profile.isBlocked(request.user):
                        return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
                    if not successor.profile.ghID() and not successor.profile.githubID:
                        return respondJson(Code.NO, error=Message.SUCCESSOR_GH_UNLINKED)
                    if successor.profile.successor == request.user:
                        if not successor.profile.successor_confirmed:
                            addMethodToAsyncQueue(
                                f"{APPNAME}.mailers.{successorInvite.__name__}", request.user, successor)
                        return respondJson(Code.NO, error=Message.SUCCESSOR_OF_PROFILE)
                    successor_confirmed = userID == BOTMAIL
                except Exception as e:
                    return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
            else:
                raise ObjectDoesNotExist()
        elif unset and request.user.profile.successor:
            successor = None
            successor_confirmed = False
        else:
            raise ObjectDoesNotExist()
        Profile.objects.filter(user=request.user).update(
            successor=successor, successor_confirmed=successor_confirmed)
        if successor and not successor_confirmed:
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{successorInvite.__name__}", successor, request.user)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
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
            raise ObjectDoesNotExist(predecessor.profile.successor)
        return renderer(request, Template.People.INVITATION, dict(predecessor=predecessor))
    except ObjectDoesNotExist as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


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
            raise ObjectDoesNotExist()

        predecessor = User.objects.get(id=predID)

        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise ObjectDoesNotExist()

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
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


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

@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def browseSearch(request: WSGIRequest):
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ''))
        limit = request.GET.get('limit', request.POST.get('limit', 10))
        excludeIDs = []
        cachekey = f'people_browse_search_{query}{request.LANGUAGE_CODE}'
        if request.user.is_authenticated:
            excludeIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}{request.user.id}"
    
        profiles = cache.get(cachekey,[])
        
        if not len(profiles):
            specials = ('topic:','type:')
            pquery = None
            is_moderator = is_mentor = is_verified = is_manager = None
            dbquery = Q()
            invalidQuery = False
            if query.startswith(specials):
                def specquerieslist(q):
                    return [Q(topics__name__iexact=q), Q()]
                commaparts = query.split(",")
                for cpart in commaparts:
                    if cpart.strip().lower().startswith(specials):    
                        special, specialq = cpart.split(':')
                        if special.strip().lower()=='type':
                            is_moderator = specialq.strip().lower() == 'moderator' or is_moderator
                            is_mentor = specialq.strip().lower() == 'mentor' or is_mentor
                            is_verified = specialq.strip().lower() == 'verified' or is_verified
                            is_manager = specialq.strip().lower() == 'manager' or is_manager
                            if is_moderator != None:
                                dbquery = Q(dbquery, is_moderator=is_moderator)
                            if is_mentor != None:
                                dbquery = Q(dbquery, is_mentor=is_mentor)
                            if is_verified != None:
                                dbquery = Q(dbquery, is_verified=is_verified)
                            if not (is_moderator or is_mentor or is_verified or is_manager):
                                invalidQuery = True
                                break
                        else:
                            dbquery = Q(dbquery, specquerieslist(specialq.strip())[list(specials).index(f"{special.strip()}:")])
                    else:
                        pquery = cpart.strip()
                        break
            else:
                pquery = query
            if pquery and not invalidQuery:
                fname, lname = convertToFLname(pquery)
                dbquery = Q(dbquery, Q(
                    Q(user__email__istartswith=pquery)
                    | Q(user__email__icontains=pquery)
                    | Q(user__first_name__istartswith=fname)
                    | Q(user__first_name__iendswith=fname)
                    | Q(user__last_name__istartswith=(lname or fname))
                    | Q(user__last_name__iendswith=(lname or fname))
                    | Q(githubID__istartswith=pquery)
                    | Q(githubID__iexact=pquery)
                    | Q(user__first_name__iexact=pquery)
                    | Q(user__last_name__iexact=pquery)
                    | Q(user__last_name__iexact=(lname or fname))
                    | Q(topics__name__iexact=pquery)
                    | Q(topics__name__istartswith=pquery)
                ))
            if not invalidQuery:
                profiles = Profile.objects.exclude(user__id__in=excludeIDs).exclude(suspended=True).exclude(to_be_zombie=True).exclude(is_active=False).filter(dbquery).distinct()[0:limit]

                if is_manager:
                    profiles=list(filter(lambda p: p.is_manager(), profiles))
                if len(profiles):
                    cache.set(cachekey, profiles, settings.CACHE_SHORT)

        if json_body:
            return respondJson(Code.OK, dict(
                profiles=list(map(lambda m: dict(
                    name=m.get_name,
                    is_verified=m.is_verified,
                    is_manager=m.is_manager(),
                    is_mentor=m.is_mentor,
                    is_moderator=m.is_moderator,
                    url=m.get_abs_link,
                    bio=m.bio,
                    imageUrl=m.get_abs_dp
                ), profiles)),
                query=query
            ))
        return rendererstr(request, Template.People.BROWSE_SEARCH, dict(profiles=profiles, query=query))
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)

@normal_profile_required
@require_GET
def create_framework(request:WSGIRequest):
    return renderer(request, Template.People.FRAMEWORK_CREATE)

@normal_profile_required
@require_JSON_body
def publish_framework(request:WSGIRequest):
    
    raise Http404()

@normal_profile_required
@require_JSON_body
def view_framework(request:WSGIRequest, frameworkID: UUID):
    
    raise Http404()


@normal_profile_required
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleAdmiration(request: WSGIRequest, userID: UUID):
    profile = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        profile = Profile.objects.get(
            user__id=userID, suspended=False, is_active=True, to_be_zombie=False)
        if request.POST['admire'] in ["true", True]:
            profile.admirers.add(request.user.profile)
        elif request.POST['admire'] in ["false", False]:
            profile.admirers.remove(request.user.profile)
        if json_body:
            return respondJson(Code.OK)
        return redirect(profile.getLink())
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if profile:
            return redirect(profile.getLink(error=Message.ERROR_OCCURRED))
        raise Http404(e)

@decode_JSON
def profileAdmirations(request, userID):
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        profile = Profile.objects.get(
            user__id=userID, suspended=False, is_active=True, to_be_zombie=False)
        admirers = profile.admirers.filter(suspended=False, is_active=True, to_be_zombie=False)
        if request.user.is_authenticated:
            admirers = request.user.profile.filterBlockedProfiles(admirers)
        if json_body:
            jadmirers = []
            for adm in admirers:
                jadmirers.append(
                    dict(
                        id=adm.get_userid,
                        name=adm.get_name,
                        dp=adm.get_dp,
                        url=adm.get_link,
                    )
                )
            return respondJson(Code.OK, dict(admirers=jadmirers))
        return render(request, Template().admirers, dict(admirers=admirers))
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)
