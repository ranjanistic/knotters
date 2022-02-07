from uuid import UUID
import re
from django.core.cache import cache
from projects.methods import addTagToDatabase
from projects.models import Tag
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
from main.strings import Action, Code, Event, Message, Template, setURLAlerts
from management.models import Management, ReportCategory
from .apps import APPNAME
from .models import ProfileSetting, ProfileSocial, ProfileTag, ProfileTopic, Topic, User, Profile
from .methods import renderer, getProfileSectionHTML, getSettingSectionHTML, convertToFLname, filterBio, rendererstr


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

    cacheKey = f"topicssearch"
    if request.user.is_authenticated:
        if excludeProfileAllTopics:
            excluding = excluding + request.user.profile.getAllTopicIds()
        elif excludeProfileTopics:
            excluding = excluding + request.user.profile.getTopicIds()
        cacheKey = f"{cacheKey}_{request.user.id}" + "".join(map(lambda i: str(i), excluding))
    
    topicslist = cache.get(cacheKey, [])

    if not len(topicslist):
        topics = Topic.objects.exclude(id__in=excluding).filter(
            Q(name__istartswith=query)
            | Q(name__iendswith=query)
            | Q(name__iexact=query)
            | Q(name__icontains=query)
        )[0:5]
        
        for topic in topics:
            topicslist.append(dict(
                id=topic.get_id,
                name=topic.name
            ))
        
        cache.set(cacheKey, topicslist, settings.CACHE_INSTANT)

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


@normal_profile_required
@require_JSON_body
def tagsSearch(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not query.strip():
            return respondJson(Code.NO)
        
        excludeIDs = []
        for tag in request.user.profile.tags.all():
            excludeIDs.append(tag.id)

        cacheKey = f"tagssearch_{request.user.id}" + "".join(map(lambda i: str(i), excludeIDs))
        tagslist = cache.get(cacheKey, [])

        if not len(tagslist):
            tags = Tag.objects.exclude(id__in=excludeIDs).filter(
                Q(name__istartswith=query)
                | Q(name__iendswith=query)
                | Q(name__iexact=query)
                | Q(name__icontains=query)
            )[0:5]
            for tag in tags:
                tagslist.append(dict(
                    id=tag.getID(),
                    name=tag.name
                ))
            cache.set(cacheKey, tagslist, settings.CACHE_INSTANT)

        return respondJson(Code.OK, dict(
            tags=tagslist
        ))
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def tagsUpdate(request: WSGIRequest) -> HttpResponse:
    json_body = request.POST.get(Code.JSON_BODY, False)
    next = None
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        addtags = request.POST.get('addtags', None)
        removetagIDs = request.POST.get('removetagIDs', None)
        profile = request.user.profile
        
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
                for topic in profile.getTopics():
                    topic.tags.add(tag)
            currentcount = currentcount + len(addtagIDs)

        if addtags:
            if not json_body:
                addtags = addtags.strip(',').split(",")
            if (currentcount + len(addtags)) <= 5:
                for addtag in addtags:
                    tag = addTagToDatabase(addtag, request.user.profile)
                    profile.tags.add(tag)
                    for topic in profile.getTopics():
                        topic.tags.add(tag)
                currentcount = currentcount + len(addtags)
            else:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.MAX_TAGS_ACHEIVED))

        if json_body:
            return respondJson(Code.OK)
        return redirect(next)
    except ObjectDoesNotExist as o:
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
            specials = ('topic:','tag:','type:')
            pquery = None
            is_moderator = is_mentor = is_verified = is_manager = None
            dbquery = Q()
            invalidQuery = False
            if query.startswith(specials):
                def specquerieslist(q):
                    return [
                        Q(topics__name__iexact=q), 
                        Q(tags__name__iexact=q), 
                        Q()
                    ]
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
                    | Q(tags__name__iexact=pquery)
                    | Q(tags__name__istartswith=pquery)
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
