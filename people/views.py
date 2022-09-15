from re import sub as re_sub
from pkgutil import extend_path
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http.response import (Http404, HttpResponse,
                                  HttpResponseBadRequest, JsonResponse)
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from main.decorators import (decode_JSON, github_only, normal_profile_required,
                             require_JSON)
from main.methods import base64ToImageFile, errorLog, respondJson
from main.strings import Code, Event, Message, Template, setURLAlerts
from management.models import ReportCategory
from projects.methods import addTagToDatabase, tagSearchList, topicSearchList
from projects.models import Tag
from ratelimit.decorators import ratelimit

from .methods import (addTopicToDatabase, convertToFLname, filterBio, filterExtendedBio,
                      getProfileSectionHTML, getSettingSectionHTML,
                      profileRenderData, renderer, rendererstr)
from .models import (Profile, ProfileSetting, ProfileSocial, ProfileTag,
                     ProfileTopic, Topic, User)
from .receivers import *
from .mailers import reportedUser, admireAlert

@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    """To render community home page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderer(request, Template.People.INDEX)


@require_GET
def profile(request: WSGIRequest, userID: str) -> HttpResponse:
    """To render a profile page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        userID (str): The user ID or nickname

    Raises:
        Http404: If the user does not exist.

    Returns:
        HttpResponse: The rendered text/html view with context.
    """
    try:
        try:
            userID = UUID(userID)
            isuuid = True
        except:
            isuuid = False

        if isuuid:
            data = profileRenderData(request, userID=userID)
        else:
            data = profileRenderData(request, nickname=userID)
            
        if not data:
            
            raise ObjectDoesNotExist(userID)

        if isuuid:
            return redirect(data["person"].profile.getLink())

        return renderer(request, Template.People.PROFILE, data)
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def profileTab(request: WSGIRequest, userID: UUID, section: str) -> HttpResponse:
    """To render a profile tab.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        userID (UUID): The user ID.
        section (str): The section to render.

    Raises:
        Http404: If the section does not exist or invalid request

    Returns:
        HttpResponse: The rendered text/html view with context.

    """
    try:
        if request.user.is_authenticated and request.user.id == userID:
            profile: Profile = request.user.profile
        else:
            profile: Profile = Profile.objects.get(
                user__id=userID)
        if request.user.is_authenticated:
            if profile.isBlocked(request.user):
                raise ObjectDoesNotExist(profile)
        return getProfileSectionHTML(profile, section, request)
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def timeline_content(request: WSGIRequest, userID: UUID) -> HttpResponse:
    """To render a timeline content.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        userID (UUID): The user ID.

    Raises:
        Http404: If the user does not exist, or invalid request

    Returns:
        HttpResponse: The rendered text/html view with context.
    """
    try:
        if request.user.is_authenticated and request.user.id == userID:
            profile = request.user.profile
        else:
            profile = Profile.objects.get(user__id=userID)
        if request.user.is_authenticated:
            if profile.isBlocked(request.user):
                raise ObjectDoesNotExist(profile)
        return rendererstr(request, Template.People.TIMELINE_CONTENT, dict(profile=profile))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_GET
def settingTab(request: WSGIRequest, section: str) -> HttpResponse:
    """To render a setting tab.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        section (str): The section to render.

    Raises:
        Http404: If the section does not exist or invalid request

    Returns:
        HttpResponse: The rendered text/html view with context.
    """
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
    """To edit a profile.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.
        section (str): The section to edit.

    Raises:
        Http404: If the section does not exist or invalid request

    Returns:
        HttpResponseRedirect: Redirects to user profile view
        JsonResponse: Responds with json object with main.strings.Code.OK or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        profile: Profile = Profile.objects.get(user=request.user)
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
                return redirect(nextlink or profile.get_link)
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
                ProfileSocial.objects.bulk_create(list(map(lambda link: ProfileSocial(
                    profile=request.user.profile, site=link), sociallinks)))
                if json_body:
                    return respondJson(Code.OK, message=Message.PROFILE_UPDATED)
                return redirect(nextlink or profile.getLink(success=Message.PROFILE_UPDATED))
            else:
                if json_body:
                    return respondJson(Code.OK)
                return redirect(nextlink or profile.get_link)
        else:
            raise ObjectDoesNotExist(section)
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)

@normal_profile_required
@require_POST
@decode_JSON
def editExtendedBio(request: WSGIRequest) -> HttpResponse:
    """To edit a ExtendedBio.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.
        section (str): The section to edit.

    Raises:
        Http404: If the section does not exist or invalid request

    Returns:
        HttpResponseRedirect: Redirects to user profile view
        JsonResponse: Responds with json object with main.strings.Code.OK or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        profile: Profile = Profile.objects.get(user=request.user)
        try:
            extended_bio = str(request.POST['ExtendedBio']).strip()
            if filterExtendedBio(extended_bio) != profile.extended_bio:
                profile.extended_bio = filterExtendedBio(extended_bio)
                profile.save()
                if json_body:
                    return respondJson(Code.OK, message=Message.PROFILE_UPDATED)
                return redirect(profile.getLink(success=Message.PROFILE_UPDATED))
            if json_body:
                return respondJson(Code.OK)
            return redirect(profile.get_link)
        except Exception as e:
            if json_body:
                return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
            return redirect(profile.getLink(error=Message.ERROR_OCCURRED))
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_POST
def accountprefs(request: WSGIRequest) -> HttpResponse:
    """To edit account preferences.

    METHODS: POST

    TODO
    """
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


@require_JSON
def topicsSearch(request: WSGIRequest) -> JsonResponse:
    """To search topics for profile.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK with topics list, or main.strings.Code.NO
    """
    try:
        query = str(request.POST["query"][:200]).strip()
        if not query:
            raise KeyError(query)
        limit = int(request.POST.get('limit', 5))
        excludeProfileTopics = request.POST.get('excludeProfileTopics', True)
        excludeProfileAllTopics = request.POST.get(
            'excludeProfileAllTopics', False)
        if not query:
            return respondJson(Code.NO)
        excluding = []

        cacheKey = f"topicssearch_{query}"
        if request.user.is_authenticated:
            if excludeProfileAllTopics:
                excluding = excluding + request.user.profile.getAllTopicIds()
            elif excludeProfileTopics:
                excluding = excluding + request.user.profile.getTopicIds()
            cacheKey = f"{cacheKey}_{request.user.id}" + \
                "".join(map(lambda i: str(i), excluding))

        return respondJson(Code.OK, dict(
            topics=topicSearchList(query, excluding, limit, cacheKey)
        ))
    except (KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
def topicsUpdate(request: WSGIRequest) -> HttpResponse:
    """To update topics for profile.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If the request is invalid

    Returns:
        HttpResponseRedirect: Redirects to profile page with relevant message
        JsonResponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    profile: Profile = request.user.profile
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        visibleTopicIDs = request.POST.get('visibleTopicIDs', None)
        addtopics = request.POST.get('addtopics', None)
        updated = False
        if not (addtopicIDs or removetopicIDs or visibleTopicIDs or addtopics):
            raise KeyError(addtopicIDs, removetopicIDs,
                           visibleTopicIDs, addtopics)

        if removetopicIDs:
            if not json_body:
                removetopicIDs = removetopicIDs.strip(',').split(',')
            ProfileTopic.objects.filter(
                profile=profile, topic__id__in=removetopicIDs).update(trashed=True)
            updated = True

        if addtopicIDs:
            if not json_body:
                addtopicIDs = addtopicIDs.strip(',').split(',')
            proftops = ProfileTopic.objects.filter(
                profile=profile)
            currentcount = proftops.filter(trashed=False).count()
            if currentcount + len(addtopicIDs) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(profile.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            newcount = currentcount + len(addtopicIDs)
            proftops.filter(topic__id__in=addtopicIDs).update(trashed=False)
            if profile.totalTopics() != newcount:
                for topic in Topic.objects.filter(id__in=addtopicIDs):
                    profile.topics.add(topic)
                updated = True

        if visibleTopicIDs and len(visibleTopicIDs) > 0:
            if len(visibleTopicIDs) > 5:
                return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
            for topic in Topic.objects.filter(id__in=visibleTopicIDs):
                profile.topics.add(topic)
            ProfileTopic.objects.filter(profile=profile).exclude(
                topic__id__in=visibleTopicIDs).update(trashed=True)
            ProfileTopic.objects.filter(
                profile=profile, topic__id__in=visibleTopicIDs).update(trashed=False)
            updated = True

        if addtopics and len(addtopics) > 0:
            count = ProfileTopic.objects.filter(
                profile=profile, trashed=False).count()
            if not json_body:
                addtopics = addtopics.strip(',').split(',')
            if count + len(addtopics) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(profile.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            profiletopics = list(map(lambda top: ProfileTopic(
                topic=addTopicToDatabase(top, profile), profile=profile),
                addtopics
            ))
            if len(profiletopics) > 0:
                ProfileTopic.objects.bulk_create(profiletopics)
                updated = True

        if updated:
            cache.delete(profile.CACHE_KEYS.topic_ids)

        if json_body:
            return respondJson(Code.OK)
        return redirect(profile.get_link)
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        return redirect(profile.getLink(error=Message.INVALID_REQUEST))
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        return redirect(profile.getLink(error=Message.ERROR_OCCURRED))


@normal_profile_required
@require_JSON
def tagsSearch(request: WSGIRequest) -> JsonResponse:
    """To search tags for profile.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If the request is invalid

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """
    try:
        query = str(request.POST['query'][:200]).strip()
        if not query:
            raise KeyError(query)
        limit = int(request.POST.get('limit', 5))
        profile: Profile = request.user.profile
        excludeIDs: list = list(profile.tags.values_list("id", flat=True))

        cacheKey = f"tagssearch_{query}" + \
            "".join(map(lambda i: i.hex, excludeIDs))

        return respondJson(Code.OK, dict(
            tags=tagSearchList(query, excludeIDs, limit, cacheKey)
        ))
    except (ObjectDoesNotExist, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def tagsUpdate(request: WSGIRequest) -> HttpResponse:
    """To update tags for profile.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If the request is invalid

    Returns:
        HttpResponseRedirect: Redirects to profile page with relevant message
        JsonReponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    next = None
    profile: Profile = request.user.profile
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        addtags = request.POST.get('addtags', None)
        removetagIDs = request.POST.get('removetagIDs', None)

        next = request.POST.get('next', profile.getLink())

        if not (addtagIDs or removetagIDs or addtags):
            return respondJson(Code.NO)

        if removetagIDs:
            if not json_body:
                removetagIDs = removetagIDs.strip(',').split(",")
            ProfileTag.objects.filter(
                profile=profile, tag__id__in=removetagIDs).delete()

        currentcount = ProfileTag.objects.filter(profile=profile).count()
        if addtagIDs:
            if not json_body:
                addtagIDs = addtagIDs.strip(',').split(",")
            if len(addtagIDs) < 1:
                if json_body:
                    return respondJson(Code.NO, error=Message.NO_TAGS_SELECTED)
                return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
            if currentcount + len(addtagIDs) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))

            for tag in Tag.objects.filter(id__in=addtagIDs):
                profile.tags.add(tag)
                map(lambda topic: topic.tags.add(tag), profile.getTopics())
            currentcount = currentcount + len(addtagIDs)

        if addtags:
            if not json_body:
                addtags = addtags.strip(',').split(",")
            if (currentcount + len(addtags)) <= 5:
                for tag in map(lambda addtag: addTagToDatabase(
                        addtag, request.user.profile), addtags):
                    profile.tags.add(tag)
                    map(lambda topic: topic.tags.add(tag), profile.getTopics())
                currentcount = currentcount + len(addtags)
            else:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.MAX_TAGS_ACHEIVED))

        if json_body:
            return respondJson(Code.OK)
        return redirect(next)
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if next:
            return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO)
        if next:
            return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
        raise Http404(e)


@normal_profile_required
def zombieProfile(request: WSGIRequest, profileID: UUID) -> JsonResponse:
    """To view zombie profile data

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.
        profileID (UUID): The profile ID. (not user ID, as it is a zombie)

    Raises:
        Http404: If the request is invalid

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK and profile data, or main.strings.Code.NO
    """
    try:
        profile = list(map(lambda p: dict(id=p[0], xp=p[1]), list(Profile.objects.filter(id=profileID,
                                                                                         successor_confirmed=True, is_zombie=True).values_list("id", "xp"))))[0]
        return respondJson(Code.OK, dict(profile=profile))
    except (ObjectDoesNotExist, ValidationError, IndexError) as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='1/s', block=True, method=(Code.POST, Code.GET))
def reportCategories(request: WSGIRequest) -> JsonResponse:
    """To get report categories

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK and report categories, or main.strings.Code.NO
    """
    try:
        return respondJson(Code.OK, dict(
            reports=list(map(lambda x: dict(id=x[0], name=x[1]), list(
                ReportCategory.get_all().values_list("id", "name"))))
        ))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON
@ratelimit(key='user_or_ip', rate='20/m', block=True, method=(Code.POST))
def reportUser(request: WSGIRequest) -> JsonResponse:
    """To report a user

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """

    try:
        report = UUID(request.POST['report'][:50])
        userID = UUID(request.POST['userID'][:50])
        user: User = User.objects.get(id=userID)
        category = ReportCategory.get_cache_one(id=report)
        if not request.user.profile.reportUser(user, category):
            raise ObjectDoesNotExist(user, category)
        reportedUser(user, category)
        return respondJson(Code.OK)
    except (ValidationError, ObjectDoesNotExist, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
@ratelimit(key='user_or_ip', rate='20/m', block=True, method=(Code.POST))
def blockUser(request: WSGIRequest) -> JsonResponse:
    """To block a user

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """
    try:
        userID = UUID(request.POST['userID'][:50])
        user: User = User.objects.get(id=userID)
        if not request.user.profile.blockUser(user):
            raise ObjectDoesNotExist(user)
        return respondJson(Code.OK)
    except (ValidationError, ObjectDoesNotExist, KeyError) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def unblockUser(request: WSGIRequest) -> JsonResponse:
    """To unblock a user

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """
    try:
        userID = UUID(request.POST['userID'][:50])
        user: User = User.objects.get(id=userID)
        if not request.user.profile.unblockUser(user):
            raise ObjectDoesNotExist(user)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@csrf_exempt
@github_only
def githubEventsListener(request: WSGIRequest, type: str, event: str) -> HttpResponse:
    """To listen to github events

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If the request is invalid

    Returns:
        HttpResponse: Responds with json object with main.strings.Code.OK, or main.strings.Code.NO
    """
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
                    member: Profile = Profile.objects.filter(
                        githubID=membership['user']['login'], is_active=True).first()
                    if member:
                        member.increaseXP(
                            by=6, reason="Github Organization Membership Accepted")
            elif action == Event.MEMBER_REMOVED:
                membership = request.POST.get('membership', None)
                if membership:
                    member: Profile = Profile.objects.filter(
                        githubID=membership['user']['login']).first()
                    if member:
                        member.decreaseXP(
                            by=6, reason="Github Organization Membership Removed")
        elif ghevent == Event.TEAMS:
            if action == Event.CREATED:
                team = request.POST.get('team', None)
                # if team:
                #     team['name']
        else:
            return HttpResponseBadRequest(ghevent)
        return HttpResponse(Code.OK)
    except Exception as e:
        errorLog(f"GH-EVENT", e)
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def browseSearch(request: WSGIRequest):
    """To search for users

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If the request is invalid

    Returns:
        HttpResponse: Responds with text/html content with users list context.
        JsonResponse: Responds with json object with main.strings.Code.OK and list of users, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ""))[
            :100].strip()

        if not query:
            raise KeyError(query)
        limit = request.GET.get('limit', request.POST.get('limit', 10))
        excludeIDs = []
        cachekey = f'people_browse_search_{query}{request.LANGUAGE_CODE}'
        if request.user.is_authenticated:
            excludeIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}" + "".join(excludeIDs)

        profiles = cache.get(cachekey, [])

        if not len(profiles):
            specials = ('topic:', 'tag:', 'xp:', 'type:')
            pquery = None
            is_moderator = is_mentor = is_verified = is_manager = None
            dbquery = Q()
            invalidQuery = False
            if query.startswith(specials):
                def specquerieslist(q):
                    return [
                        Q(topics__name__iexact=q),
                        Q(tags__name__iexact=q),
                        Q(xp__gte=q),
                        Q()
                    ]
                commaparts = query.split(",")
                for cpart in commaparts:
                    if cpart.strip().lower().startswith(specials):
                        special, specialq = cpart.split(':')
                        if special.strip().lower() == 'type':
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
                            dbquery = Q(dbquery, specquerieslist(specialq.strip())[
                                        list(specials).index(f"{special.strip()}:")])
                    else:
                        pquery = cpart.strip()
                        break
            else:
                pquery = query
            if pquery and not invalidQuery:
                fname, lname = convertToFLname(pquery)
                dbquery = Q(dbquery, Q(
                    Q(user__email__istartswith=pquery)
                    | Q(user__first_name__istartswith=fname)
                    | Q(user__first_name__iendswith=fname)
                    | Q(user__last_name__istartswith=(lname or fname))
                    | Q(user__last_name__iendswith=(lname or fname))
                    | Q(nickname__istartswith=pquery)
                    | Q(nickname__iexact=pquery)
                    | Q(topics__name__istartswith=pquery)
                    | Q(tags__name__istartswith=pquery)
                    | Q(user__email__icontains=pquery)
                ))
            if not invalidQuery:
                profiles = Profile.objects.exclude(user__id__in=excludeIDs).exclude(suspended=True).exclude(
                    to_be_zombie=True).exclude(is_active=False).filter(dbquery).distinct()[:limit]

                if is_manager:
                    profiles = list(filter(lambda p: p.is_manager(), profiles))

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
                    extended_bio=m.extended_bio,
                    imageUrl=m.get_abs_dp
                ), profiles)),
                query=query
            ))

        return rendererstr(request, Template.People.BROWSE_SEARCH, dict(profiles=profiles, query=query))
    except KeyError:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        pass
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        pass
    raise Http404(e)


@normal_profile_required
@require_GET
def create_framework(request: WSGIRequest):
    """To create a framework
    TODO
    """
    return renderer(request, Template.People.FRAMEWORK_CREATE)


@normal_profile_required
@require_JSON
def publish_framework(request: WSGIRequest):
    """To publish a framework
    TODO
    """
    raise Http404()


@normal_profile_required
@require_JSON
def view_framework(request: WSGIRequest, frameworkID: UUID):
    """To view a framework
    TODO
    """
    raise Http404()


@normal_profile_required
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleAdmiration(request: WSGIRequest, userID: UUID) -> JsonResponse:
    """To toggle profile admiration

    Args:
        request (WSGIRequest): The request object
        userID (UUID): The user's ID

    Raises:
        Http404: If request is invalid

    Returns:
        HttpResponseRedirect: Redirect to the profile page with relvent message
        JsonResponse: The response json object with main.strings.Code.OK, or main.strings.Code.NO
    """
    profile = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        profile: Profile = Profile.objects.get(
            user__id=userID, suspended=False, is_active=True, to_be_zombie=False)
        if request.POST['admire'] in ["true", True]:
            profile.admirers.add(request.user.profile)
            admireAlert(profile, request)
        elif request.POST['admire'] in ["false", False]:
            profile.admirers.remove(request.user.profile)
        if json_body:
            return respondJson(Code.OK)
        return redirect(profile.get_link)
    except (ObjectDoesNotExist, KeyError, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if profile:
            return redirect(profile.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if profile:
            return redirect(profile.getLink(error=Message.ERROR_OCCURRED))
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='1/s', block=True)
@decode_JSON
def profileAdmirations(request: WSGIRequest, userID: UUID) -> HttpResponse:
    """To view a profile's admirers list

    Args:
        request (WSGIRequest): The request object
        userID (UUID): The user's ID

    Raises:
        Http404: If request is invalid

    Returns:
        HttpResponse: The response text/html of admirers list view
        JsonResponse: The response json object with main.strings.Code.OK and list of admirers, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        profile: Profile = Profile.objects.get(
            user__id=userID, suspended=False, is_active=True, to_be_zombie=False)
        admirers: list = profile.admirers.filter(
            suspended=False, is_active=True, to_be_zombie=False)
        if request.user.is_authenticated:
            admirers: list = request.user.profile.filterBlockedProfiles(
                admirers)
        if json_body:
            jadmirers = list(map(lambda adm: dict(
                id=adm.get_userid,
                name=adm.get_name,
                dp=adm.get_dp,
                url=adm.get_link,
            ), admirers))
            return respondJson(Code.OK, dict(admirers=jadmirers))
        return render(request, Template().admirers, dict(admirers=admirers))
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        errorLog(e)
        raise Http404(e)



