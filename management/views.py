from datetime import timedelta
from uuid import UUID

from compete.models import Competition
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import validate_email
from django.db.models import Q
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from main.decorators import (manager_only, normal_profile_required,
                             require_JSON, require_JSON_body)
from main.methods import (addMethodToAsyncQueue, base64ToImageFile, errorLog,
                          respondJson, respondRedirect)
from main.strings import (COMPETE, MODERATION, URL, Action, Code, Message,
                          Template)
from moderation.mailers import moderationAssignedAlert
from moderation.methods import (assignModeratorToObject,
                                getModeratorToAssignModeration)
from moderation.models import Moderation
from people.methods import addTopicToDatabase
from people.models import Profile, ReportedUser, Topic
from projects.methods import addCategoryToDatabase, addTagToDatabase
from projects.models import Category, Tag
from ratelimit.decorators import ratelimit

from management.mailers import (managementInvitationAccepted,
                                managementInvitationSent,
                                managementPersonRemoved)

from .apps import APPNAME
from .methods import (competitionManagementRenderData, createCompetition,
                      labelRenderData, renderer, rendererstr)
from .models import (ContactCategory, ContactRequest, Feedback, Management,
                     ManagementInvitation, Report)


@manager_only
@require_GET
# @cache_page(settings.CACHE_LONG)
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Management.INDEX)


@manager_only
@require_GET
# @cache_page(settings.CACHE_LONG)
def community(request: WSGIRequest):
    return renderer(request, Template.Management.COMMUNITY_INDEX)


@manager_only
@require_GET
def moderators(request: WSGIRequest):
    try:
        mgm = Management.objects.get(profile=request.user.profile)
        moderators = mgm.people.filter(
            is_moderator=True, to_be_zombie=False, is_active=True, suspended=False).order_by('-xp')[0:10]
        profiles = mgm.people.filter(is_moderator=False, is_mentor=False,
                                     to_be_zombie=False, is_active=True, suspended=False).order_by('-xp')[0:10]
        profiles = list(filter(lambda x: not x.is_manager(), profiles))
        return renderer(request, Template.Management.COMMUNITY_MODERATORS, dict(moderators=moderators, profiles=profiles))
    except Exception as e:
        raise Http404(e)


@manager_only
@require_JSON_body
def searchEligibleModerator(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        mgm = Management.objects.get(profile=request.user.profile)
        profile = mgm.people.filter(Q(
            Q(is_active=True,
                suspended=False, to_be_zombie=False, is_moderator=False, is_mentor=False,),
            Q(user__email__startswith=query)
            | Q(user__first_name__startswith=query)
            | Q(githubID__startswith=query)
        )).first()
        if not profile:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        if profile.isBlocked(request.user) or profile.is_manager():
            raise Exception("blocked or mgr", profile, request.user)
        return respondJson(Code.OK, dict(mod=dict(
            id=profile.user.id,
            userID=profile.getUserID(),
            name=profile.getName(),
            email=profile.getEmail(),
            url=profile.getLink(),
            dp=profile.getDP(),
        )))
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON_body
def removeModerator(request: WSGIRequest):
    try:
        modID = request.POST.get('modID', None)
        if not modID or modID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = Management.objects.get(profile=request.user.profile)
        moderators = mgm.people.filter(
            user__id=modID, is_moderator=True).values_list('id', flat=True)
        if not len(moderators):
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        unresolved = Moderation.objects.filter(
            moderator__user__id=modID, resolved=False)
        for mod in unresolved:
            if mod.requestor == request.user.profile:
                onlyModProfiles = None
                preferModProfiles = []
                if mod.internal_mod:
                    onlyModProfiles = [mgm.people.filter(
                        user__id=modID, is_moderator=True, to_be_zombie=False, is_active=True, suspended=False)]
                else:
                    if mod.project or mod.coreproject:
                        preferModProfiles = Profile.objects.filter(
                            is_moderator=True, suspended=False, is_active=True, to_be_zombie=False, topics__in=mod.object.category.topics).distinct()
                moderator = getModeratorToAssignModeration(
                    mod.type, mod.object, ignoreModProfiles=[mod.moderator],
                    onlyModProfiles=onlyModProfiles,
                    preferModProfiles=preferModProfiles,
                    internal=mod.internal_mod
                )
                if moderator:
                    mod.moderator = moderator
                    mod.requestOn = timezone.now()
                    mod.save()
                    addMethodToAsyncQueue(
                        f"{MODERATION}.mailers.{moderationAssignedAlert.__name__}", mod)
                else:
                    return respondJson(Code.NO, error=Message.NO_INTERNAL_MODERATORS)
            else:
                return respondJson(Code.NO, error=Message.PENDING_MODERATIONS_EXIST)
        moderators = Profile.objects.filter(
            id__in=list(moderators)).update(is_moderator=False)
        if moderators == 0:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def addModerator(request: WSGIRequest):
    try:
        userID = request.POST.get('userID', None)
        if not userID or userID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = Management.objects.get(profile=request.user.profile)
        profiles = mgm.people.filter(user__id=userID, is_moderator=False, is_mentor=False,
                                     suspended=False, to_be_zombie=False, is_active=True).values_list('id', flat=True)
        profiles = Profile.objects.filter(
            id__in=list(profiles)).update(is_moderator=True)
        if profiles == 0:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@manager_only
@require_GET
def mentors(request: WSGIRequest):
    try:
        mgm = Management.objects.get(profile=request.user.profile)
        mentors = mgm.people.filter(
            is_mentor=True, to_be_zombie=False, is_active=True, suspended=False).order_by('-xp')[0:10]
        profiles = mgm.people.filter(is_mentor=False, is_moderator=False,
                                     to_be_zombie=False, is_active=True, suspended=False).order_by('-xp')[0:10]
        profiles = list(filter(lambda x: not x.is_manager(), profiles))
        return renderer(request, Template.Management.COMMUNITY_MENTORS, dict(mentors=mentors, profiles=profiles))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_JSON_body
def searchEligibleMentor(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        mgm = Management.objects.get(profile=request.user.profile)
        profile = mgm.people.filter(Q(
            Q(is_active=True,
                suspended=False, to_be_zombie=False, is_mentor=False, is_moderator=False),
            Q(user__email__startswith=query)
            | Q(user__first_name__startswith=query)
            | Q(githubID__startswith=query)
        )).first()
        if not profile:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        if profile.isBlocked(request.user):
            raise Exception('blocked:', profile, request.user)
        return respondJson(Code.OK, dict(mnt=dict(
            id=profile.user.id,
            userID=profile.getUserID(),
            name=profile.getName(),
            email=profile.getEmail(),
            url=profile.getLink(),
            dp=profile.getDP(),
        )))
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON_body
def removeMentor(request: WSGIRequest):
    try:
        mntID = request.POST.get('mntID', None)
        if not mntID or mntID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = Management.objects.get(profile=request.user.profile)
        mentors = mgm.people.filter(
            user__id=mntID, is_mentor=True).values_list('id', flat=True)
        mentors = Profile.objects.filter(
            id__in=list(mentors)).update(is_mentor=False)
        if mentors == 0:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON_body
def addMentor(request: WSGIRequest):
    try:
        userID = request.POST.get('userID', None)
        if not userID or userID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = Management.objects.get(profile=request.user.profile)
        profiles = mgm.people.filter(user__id=userID, is_mentor=False, is_moderator=False,
                                     suspended=False, to_be_zombie=False, is_active=True).values_list('id', flat=True)
        profiles = Profile.objects.filter(
            id__in=list(profiles)).update(is_mentor=True)
        if profiles == 0:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
# @cache_page(settings.CACHE_LONG)
def labels(request: WSGIRequest):
    return renderer(request, Template.Management.COMMUNITY_LABELS)


@manager_only
@require_GET
def labelType(request: WSGIRequest, type: str):
    try:
        mgm = Management.objects.get(profile=request.user.profile)
        if type == Code.TOPIC:
            topics = Topic.objects.filter(
                Q(Q(creator__in=mgm.people.all()) | Q(creator=request.user.profile)))
            return rendererstr(request, Template.Management.COMMUNITY_LABELS_TOPICS, dict(topics=topics))
        if type == Code.CATEGORY:
            categories = Category.objects.filter(
                Q(Q(creator__in=mgm.people.all()) | Q(creator=request.user.profile)))
            return rendererstr(request, Template.Management.COMMUNITY_LABELS_CATEGORIES, dict(categories=categories))
        if type == Code.TAG:
            tags = Tag.objects.filter(
                Q(Q(creator__in=mgm.people.all()) | Q(creator=request.user.profile)))
            return rendererstr(request, Template.Management.COMMUNITY_LABELS_TAGS, dict(tags=tags))
        raise Exception('Invalid label')
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_GET
def label(request: WSGIRequest, type: str, labelID: UUID):
    try:
        data = labelRenderData(request, type, labelID)
        if not data:
            raise ObjectDoesNotExist(type, labelID)
        if type == Code.TOPIC:
            return renderer(request, Template.Management.COMMUNITY_TOPIC, data)
        if type == Code.CATEGORY:
            return renderer(request, Template.Management.COMMUNITY_CATEGORY, data)
        raise ObjectDoesNotExist('Invalid label')
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_JSON_body
def labelCreate(request: WSGIRequest, type: str):
    try:
        name = request.POST['name']
        if type == Code.TOPIC:
            label = addTopicToDatabase(name, request.user.profile)
        elif type == Code.CATEGORY:
            label = addCategoryToDatabase(name, request.user.profile)
        elif type == Code.TAG:
            label = addTagToDatabase(name, request.user.profile)
        else:
            return respondJson(Code.NO)
        return respondJson(Code.OK, dict(label=dict(id=label.get_id, name=label.name)))
    except:
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def labelUpdate(request: WSGIRequest, type: str, labelID: UUID):
    try:
        mgm = Management.objects.get(profile=request.user.profile)
        name = request.POST['name']
        if type == Code.TAG:
            Tag.objects.filter(Q(id=labelID), Q(Q(creator__in=[mgm.people.all()]) | Q(
                creator=request.user.profile))).update(name=name)
        elif type == Code.TOPIC:
            Topic.objects.filter((Q(id=labelID), Q(Q(creator__in=[mgm.people.all()]) | Q(
                creator=request.user.profile)))).update(name=name)
        elif type == Code.CATEGORY:
            Category.objects.filter((Q(id=labelID), Q(Q(creator__in=[mgm.people.all()]) | Q(
                creator=request.user.profile)))).update(name=name)
        else:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except:
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def labelDelete(request: WSGIRequest, type: str, labelID: UUID):
    try:
        mgm = Management.objects.get(profile=request.user.profile)
        if type == Code.TOPIC:
            topic = Topic.objects.filter(Q(id=labelID), Q(
                Q(creator__in=[mgm.people.all()]) | Q(creator=request.user.profile))).first()
            if topic.isDeletable:
                topic.delete()
        elif type == Code.CATEGORY:
            category = Category.objects.filter(Q(id=labelID), Q(
                Q(creator__in=[mgm.people.all()]) | Q(creator=request.user.profile))).first()
            if category.isDeletable:
                category.delete()
        elif type == Code.TAG:
            Tag.objects.filter(Q(id=labelID), Q(
                Q(creator__in=[mgm.people.all()]) | Q(creator=request.user.profile))).delete()
        else:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except:
        return respondJson(Code.NO)


def contact_categories(request: WSGIRequest) -> HttpResponse:
    try:
        cacheKey = 'contact_categories'
        categories = cache.get(cacheKey, [])
        if not len(categories):
            cats = ContactCategory.objects.filter(disabled=False)
            for cat in cats:
                categories.append(dict(id=cat.id, name=cat.name))
            if len(categories):
                cache.set(cacheKey, categories, settings.CACHE_INSTANT)
        return respondJson(Code.OK, dict(categories=categories))
    except (ObjectDoesNotExist, KeyError, ValidationError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_JSON
@ratelimit(key='user_or_ip', rate='10/m', block=True, method=(Code.POST))
def contact_subm(request: WSGIRequest) -> HttpResponse:
    try:
        contactCategoryID = request.POST['contactCategoryID']
        contactCategory = ContactCategory.objects.get(id=contactCategoryID)
        senderName = request.POST['senderName']
        senderEmail = request.POST['senderEmail']
        validate_email(senderEmail)
        senderMessage = request.POST['senderMessage']
        created = ContactRequest.objects.create(
            contactCategory=contactCategory, senderName=senderName, senderEmail=senderEmail, message=senderMessage)
        if not created:
            raise Exception('Failed to create contact request')
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
def competitions(request: WSGIRequest) -> HttpResponse:
    try:
        competes = Competition.objects.filter(creator=request.user.profile)
        return renderer(request, Template.Management.COMP_INDEX, dict(competes=competes))
    except Exception as e:
        raise Http404(e)


@manager_only
@require_GET
def competition(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        data = competitionManagementRenderData(request, compID)
        if not data:
            raise ObjectDoesNotExist(compID)
        return renderer(request, Template.Management.COMP_COMPETE, data)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_JSON_body
def searchTopic(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        topic = Topic.objects.filter(
            name__istartswith=query.capitalize()).first()
        return respondJson(Code.OK, dict(topic=dict(
            id=topic.id,
            name=topic.name
        )))
    except Exception as e:
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def searchMentor(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        excludeIDs = request.POST.get('excludeIDs', [])
        mgm = Management.objects.get(profile=request.user.profile)
        profile = mgm.people.exclude(user__id__in=excludeIDs).filter(
            Q(
                Q(is_active=True,
                  suspended=False, to_be_zombie=False, is_mentor=True),
                Q(user__email__startswith=query)
                | Q(user__first_name__startswith=query)
                | Q(githubID__startswith=query)
            )
        ).first()
        if profile.isBlocked(request.user):
            raise Exception()
        return respondJson(Code.OK, dict(mnt=dict(
            id=profile.user.id,
            userID=profile.getUserID(),
            name=profile.getName(),
            email=profile.getEmail(),
            url=profile.getLink(),
            dp=profile.getDP(),
        )))
    except Exception as e:
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def searchModerator(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        excludeIDs = request.POST.get('excludeIDs', [])
        internalOnly = request.POST.get('internalOnly', True)
        if internalOnly:
            mgm = Management.objects.get(profile=request.user.profile)
            profile = mgm.people.exclude(user__id__in=excludeIDs).filter(
                Q(
                    Q(is_active=True,
                      suspended=False, to_be_zombie=False, is_moderator=True),
                    Q(user__email__startswith=query)
                    | Q(user__first_name__startswith=query)
                    | Q(githubID__startswith=query)
                )
            ).first()
        else:
            profile = Profile.objects.exclude(user__id__in=excludeIDs).filter(
                Q(
                    Q(is_active=True,
                      suspended=False, to_be_zombie=False, is_moderator=True),
                    Q(user__email__startswith=query)
                    | Q(user__first_name__startswith=query)
                    | Q(githubID__startswith=query)
                )
            ).first()
        if profile:
            if profile.isBlocked(request.user):
                raise Exception('mgm modsearch blocked: ',
                                profile, request.user)
            return respondJson(Code.OK, dict(mod=dict(
                id=profile.user.id,
                userID=profile.getUserID(),
                name=profile.getName(),
                email=profile.getEmail(),
                url=profile.getLink(),
                dp=profile.getDP(),
            )))
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
# @cache_page(settings.CACHE_SHORT)
def createCompete(request: WSGIRequest) -> HttpResponse:
    data = dict()
    lastcomp = Competition.objects.filter(creator=request.user.profile).exclude(
        associate__isnull=True).exclude(associate__exact='').order_by("-modifiedOn").first()
    if lastcomp:
        data = dict(associate=lastcomp.get_associate)
    return renderer(request, Template.Management.COMP_CREATE, data)


@manager_only
@require_POST
def submitCompetition(request) -> HttpResponse:
    compete = None
    try:
        title = str(request.POST["comptitle"]).strip()
        tagline = str(request.POST["comptagline"]).strip()
        shortdesc = str(request.POST["compshortdesc"]).strip()
        desc = str(request.POST["compdesc"]).strip()
        modID = str(request.POST['compmodID']).strip()
        useAssociate = request.POST.get('useAssociate', False)
        startAt = request.POST['compstartAt']
        endAt = request.POST['compendAt']
        eachTopicMaxPoint = int(request.POST['compeachTopicMaxPoint'])
        max_grouping = int(request.POST['compmaxgrouping'])
        reg_fee = int(request.POST.get('compregfee', 0))
        fee_link = str(request.POST.get('compfeelink', ""))
        topicIDs = str(request.POST['comptopicIDs']
                       ).strip().strip(',').split(',')
        judgeIDs = str(request.POST['compjudgeIDs']
                       ).strip().strip(',').split(',')
        taskSummary = str(request.POST['comptaskSummary']).strip()
        taskDetail = str(request.POST['comptaskDetail']).strip()
        taskSample = str(request.POST['comptaskSample']).strip()

        qualifier_id = str(request.POST.get(
            'qualifier-competition-id', '')).strip()
        qualifier_rank = 0

        if qualifier_id:
            qualifier_rank = int(request.POST['qualifier-competition-rank'])
            if qualifier_rank < 1:
                return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.INVALID_QUALIFIER_RANK)

        perks = []
        for key in request.POST.keys():
            if str(key).startswith('compperk'):
                perk = str(request.POST[key]).strip()
                if perk:
                    perks.append(perk)

        if not (title and
                tagline and
                shortdesc and
                desc and
                modID and
                startAt and
                endAt and
                eachTopicMaxPoint > 0 and
                max_grouping > 0 and
                len(topicIDs) > 0 and
                len(judgeIDs) > 0 and
                len(perks) > 0 and
                taskSummary and
                taskDetail and
                taskSample):
            raise Exception("Invalid details")
        if reg_fee > 0 and not fee_link:
            raise Exception("Invalid details")
        if Competition.objects.filter(title__iexact=title).exists():
            return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.COMP_TITLE_EXISTS)

        if startAt >= endAt:
            return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.INVALID_TIME_PAIR)

        if modID.replace('-', '').lower() in list(map(lambda j: j.replace('-', '').lower(), judgeIDs)):
            return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.INVALID_TIME_PAIR)
        qualifier = None
        if qualifier_id:
            qualifier = Competition.objects.get(
                id=qualifier_id, hidden=False, is_draft=False)
        compete = createCompetition(
            creator=request.user.profile,
            title=title,
            tagline=tagline,
            shortdescription=shortdesc,
            description=desc,
            perks=perks,
            startAt=startAt,
            endAt=endAt,
            eachTopicMaxPoint=eachTopicMaxPoint,
            topicIDs=topicIDs,
            judgeIDs=judgeIDs,
            taskSummary=taskSummary,
            taskDetail=taskDetail,
            taskSample=taskSample,
            max_grouping=max_grouping,
            reg_fee=reg_fee,
            fee_link=fee_link,
            qualifier=qualifier,
            qualifier_rank=qualifier_rank
        )
        if not compete:
            raise Exception("Competition not created")
        banner = False
        try:
            bannerdata = request.POST['compbanner']
            bannerfile = base64ToImageFile(bannerdata)
            if bannerfile:
                compete.banner = bannerfile
                banner = True
        except Exception as e:
            pass

        associate = False
        try:
            associatedata = request.POST['compassociate']
            associatefile = base64ToImageFile(associatedata)
            if associatefile:
                compete.associate = associatefile
                associate = True
        except Exception as e:
            pass

        if not associate and useAssociate:
            lastcomp = Competition.objects.exclude(id=compete.id).filter(
                creator=request.user.profile).order_by("-modifiedOn").first()
            if lastcomp:
                compete.associate = str(lastcomp.associate)
                associate = True

        if associate or banner:
            compete.save()

        mod = Profile.objects.get(
            user__id=modID, is_moderator=True, is_active=True, to_be_zombie=False, suspended=False)
        assigned = assignModeratorToObject(
            COMPETE, compete, mod, "Competition")
        if not assigned:
            return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.INVALID_MODERATOR)
        return redirect(compete.getManagementLink(alert=Message.COMP_CREATED))
    except Exception as e:
        if compete:
            compete.delete()
        errorLog(e)
        return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON
def editCompetition(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        compete = Competition.objects.get(
            id=compID, creator=request.user.profile)
        changed = False
        if compete.canBeEdited():
            title = str(request.POST.get("comptitle", '')).strip()
            if title and title != compete.title:
                compete.title = title
            tagline = str(request.POST.get("comptagline", '')).strip()
            if tagline and tagline != compete.tagline:
                compete.tagline = tagline
            shortdescription = str(
                request.POST.get("compshortdesc", '')).strip()
            if shortdescription and shortdescription != compete.shortdescription:
                compete.shortdescription = shortdescription

            description = str(request.POST.get("compdesc", '')).strip()
            if description and description != compete.description:
                compete.description = description

            startAt = request.POST.get("compstartAt", None)
            if startAt and startAt != compete.startAt:
                compete.startAt = startAt

            endAt = request.POST.get("compendAt", None)
            if endAt and endAt != compete.endAt and endAt > compete.startAt:
                compete.endAt = endAt

            eachTopicMaxPoint = request.POST.get("compeachTopicMaxPoint", None)
            if eachTopicMaxPoint and eachTopicMaxPoint != compete.eachTopicMaxPoint:
                compete.eachTopicMaxPoint = eachTopicMaxPoint
            maxGrouping = int(request.POST.get("compMaxGrouping", 1))
            if maxGrouping and maxGrouping != compete.max_grouping:
                compete.max_grouping = maxGrouping
            if compete.reg_fee:
                reg_fee = request.POST.get("compregfee", None)
                if reg_fee and reg_fee != compete.reg_fee:
                    compete.reg_fee = reg_fee
                feelink = request.POST.get("compfeelink", None)
                if feelink and feelink != compete.feelink:
                    compete.feelink = feelink
            taskSummary = request.POST.get("comptaskSummary", None)
            if taskSummary and taskSummary != compete.taskSummary:
                compete.taskSummary = taskSummary
            taskDetail = request.POST.get("comptaskDetail", None)
            if taskDetail and taskDetail != compete.taskDetail:
                compete.taskDetail = taskDetail
            taskSample = request.POST.get("comptaskSample", None)
            if taskSample and taskSample != compete.taskSample:
                compete.taskSample = taskSample

            topicIDs = request.POST.get("comptopicIDs", None)
            if topicIDs and len(topicIDs) > 0:
                topics = Topic.objects.filter(id__in=topicIDs)
                compete.topics.set(topics)

            try:
                bannerdata = request.POST['compbanner']
                bannerfile = base64ToImageFile(bannerdata)
                if bannerfile:
                    compete.banner = bannerfile
            except Exception as e:
                pass

            try:
                associatedata = request.POST['compassociate']
                associatefile = base64ToImageFile(associatedata)
                if associatefile:
                    compete.associate = associatefile
            except Exception as e:
                pass
            changed = True

        if compete.canChangeModerator():
            modID = request.POST.get("compmodID", None)
            if modID:
                newmod = Profile.objects.filter(
                    user__id=modID, is_moderator=True, is_active=True, to_be_zombie=False, suspended=False).first()
                if newmod:
                    moderation = compete.moderation()
                    moderation.moderator = newmod
                    moderation.save()
                changed = True

        if compete.canChangeJudges():
            judgeIDs = request.POST.get("compjudgeIDs", None)
            if judgeIDs and len(judgeIDs) > 0:
                newjudges = Profile.objects.filter(
                    user__id__in=judgeIDs, is_mentor=True, is_active=True, to_be_zombie=False, suspended=False)
                compete.judges.set(newjudges)
                changed = True

        if not changed:
            raise ObjectDoesNotExist('cannot edit compete', compete)
        compete.save()
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON_body
def draftDeleteCompete(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        compete = Competition.objects.get(
            id=compID, creator=request.user.profile)
        delete = request.POST.get('delete', False)
        draft = request.POST.get('draft', None)
        confirmed = request.POST.get('confirmed', False)
        if not confirmed:
            raise ObjectDoesNotExist('not confirmed', compete)

        if draft is not None:
            if draft and not compete.canBeSetToDraft():
                raise ObjectDoesNotExist('cannot set to draft', compete)
            compete.is_draft = draft
            compete.save()
        elif delete:
            if not compete.canBeDeleted():
                raise ObjectDoesNotExist('cannot delete compete', compete)
            compete.judges.clear()
            compete.delete()
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
# @cache_page(settings.CACHE_LONG)
def reportFeedbacks(request: WSGIRequest):
    return renderer(request, Template.Management.REPORTFEED_INDEX)


@require_JSON_body
def createReport(request: WSGIRequest) -> JsonResponse:
    email = request.POST.get('email', None)
    email = str(email).strip()
    reporter = None
    if email and str(email).strip():
        if request.user.is_authenticated and email == request.user.email:
            reporter = request.user.profile
        else:
            reporter = Profile.objects.filter(
                user__email__iexact=email).first()
    summary = request.POST.get('summary', '')
    detail = request.POST.get('detail', '')
    report = Report.objects.create(
        reporter=reporter, summary=summary, detail=detail)
    return respondJson(Code.OK if report else Code.NO, error=Message.ERROR_OCCURRED if not report else '')


@require_JSON_body
def createFeedback(request: WSGIRequest):
    email = request.POST.get('email', None)
    email = str(email).strip()
    feedbacker = None
    if email and str(email).strip():
        if request.user.is_authenticated and email == request.user.email:
            feedbacker = request.user.profile
        else:
            feedbacker = Profile.objects.filter(
                user__email__iexact=email).first()
    detail = request.POST.get('detail', '')
    feedback = Feedback.objects.create(feedbacker=feedbacker, detail=detail)
    return respondJson(Code.OK if feedback else Code.NO, error=Message.ERROR_OCCURRED if not feedback else '')


@manager_only
@require_GET
def reportfeedType(request: WSGIRequest, type: str):
    try:
        mgm = Management.objects.get(profile=request.user.profile)
        if type == Code.REPORTS:
            userreports = ReportedUser.objects.filter(user__id__in=mgm.people.filter(
                suspended=False, is_active=True, to_be_zombie=False).values_list('user__id', flat=True))
            return rendererstr(request, Template.Management.REPORTFEED_REPORTS, dict(reports=[], userreports=userreports))
        elif type == Code.FEEDBACKS:
            feedbacks = Feedback.objects.filter()
            return rendererstr(request, Template.Management.REPORTFEED_FEEDBACKS, dict(feedbacks=feedbacks))
        else:
            raise Exception(type)
    except Exception as e:
        raise Http404(e)


@manager_only
@require_GET
def reportfeedTypeID(request: WSGIRequest, type: str, ID: UUID):
    try:
        if type == Code.REPORTS:
            report = Report.objects.get(id=ID)
            return rendererstr(request, Template.Management.REPORTFEED_REPORT, dict(report=report))
        elif type == Code.FEEDBACKS:
            feedback = Feedback.objects.get(id=ID)
            return rendererstr(request, Template.Management.REPORTFEED_FEEDBACK, dict(feedback=feedback))
        else:
            raise Exception(type)
    except Exception as e:
        raise Http404(e)


@manager_only
@require_JSON_body
def sendPeopleInvite(request: WSGIRequest):
    try:
        action = request.POST['action']
        if action == Action.CREATE:
            email = request.POST['email'].lower()
            if (request.user.email == email) or (email in request.user.emails()):
                return respondJson(Code.NO, error=Message.INVALID_REQUEST)
            receiver = Profile.objects.get(
                user__email=email, suspended=False, is_active=True, to_be_zombie=False)
            if request.user.profile.management().people.filter(id=receiver.id).exists():
                return respondJson(Code.NO, error=Message.ALREADY_EXISTS)
            if receiver.isBlocked(request.user):
                return respondJson(Code.NO, error=Message.USER_NOT_EXIST)

            inv, created = ManagementInvitation.objects.get_or_create(
                management=request.user.profile.management(),
                sender=request.user.profile,
                resolved=False,
                receiver=receiver,
                defaults=dict(
                    resolved=False
                )
            )
            if not created:
                if inv.expired:
                    inv.expiresOn = timezone.now() + timedelta(days=1)
                    inv.save()
                    addMethodToAsyncQueue(
                        f"{APPNAME}.mailers.{managementInvitationSent.__name__}", inv)
                else:
                    return respondJson(Code.NO, error=Message.ALREADY_INVITED)
        elif action == Action.REMOVE:
            invID = request.POST['inviteID']
            inv = ManagementInvitation.objects.get(id=invID, resolved=False)
            inv.delete()
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def peopleMGMInvitation(request: WSGIRequest, inviteID: UUID):
    try:
        invitation = ManagementInvitation.objects.get(id=inviteID,
                                                      receiver=request.user.profile, expiresOn__gt=timezone.now(),
                                                      resolved=False,
                                                      management__profile__suspended=False,
                                                      management__profile__is_active=True
                                                      )
        return renderer(request, Template.Management.INVITATION,
                        dict(invitation=invitation))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        raise Http404(e)


@normal_profile_required
@require_JSON_body
def peopleMGMInvitationAction(request: WSGIRequest, inviteID: UUID):
    try:
        action = request.POST['action']
        invitation = ManagementInvitation.objects.get(id=inviteID,
                                                      receiver=request.user.profile, expiresOn__gt=timezone.now(),
                                                      resolved=False,
                                                      management__profile__suspended=False,
                                                      management__profile__is_active=True
                                                      )
        done = False
        accept = False
        if action == Action.ACCEPT:
            accept = True
            done = invitation.accept()
        elif action == Action.DECLINE:
            done = invitation.decline()
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.JOINED_MANAGEMENT
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{managementInvitationAccepted.__name__}", invitation)
        else:
            message = Message.DECLINED_JOIN_MANAGEMENT
        return redirect(invitation.management.getLink(message=message))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        raise Http404(e)


@normal_profile_required
@require_JSON_body
def peopleMGMRemove(request: WSGIRequest):
    try:
        userID = request.POST['userID']
        mgmID = request.POST['mgmID']

        person = Profile.objects.get(user__id=userID)
        mgm = Management.objects.get(id=mgmID)

        if not (request.user.profile == person or request.user.profile == mgm.profile):
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if person.is_moderator:
            if Moderation.objects.filter(competition__creator=mgm.profile, moderator=person, resolved=False).exists():
                return respondJson(Code.NO, error=Message.PENDING_MODERATIONS_EXIST)

        done = person.removeFromManagement(mgm.id)
        if not done:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)

        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{managementPersonRemoved.__name__}", mgm, person)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
