from datetime import timedelta
from uuid import UUID

from compete.models import Competition
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.core.validators import validate_email
from django.db.models import Q
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from main.decorators import manager_only, normal_profile_required, require_JSON
from main.methods import (base64ToImageFile, errorLog, respondJson,
                          respondRedirect)
from main.strings import COMPETE, URL, Action, Code, Message, Template
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
from .receivers import *


@manager_only
@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    """To render the index page of management

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The rendered text/html view
    """
    return renderer(request, Template.Management.INDEX)


@manager_only
@require_GET
def community(request: WSGIRequest):
    """To render the community view of management

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The rendered text/html view
    """
    return renderer(request, Template.Management.COMMUNITY_INDEX)


@manager_only
@require_GET
def moderators(request: WSGIRequest):
    """To render the moderators view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The rendered text/html view
    """
    try:
        mgm = request.user.profile.management()
        moderators = mgm.people.filter(
            is_moderator=True, to_be_zombie=False, is_active=True, suspended=False).order_by('-xp')[0:10]
        profiles = mgm.people.filter(is_moderator=False, is_mentor=False,
                                     to_be_zombie=False, is_active=True, suspended=False).order_by('-xp')[0:10]
        profiles = list(filter(lambda x: not x.is_manager(), profiles))
        return renderer(request, Template.Management.COMMUNITY_MODERATORS, dict(moderators=moderators, profiles=profiles))
    except Exception as e:
        raise Http404(e)


@manager_only
@require_JSON
def searchEligibleModerator(request: WSGIRequest) -> JsonResponse:
    """To search for an eligible user to be a moderator, based on the search query.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.query (str): The search query

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK and a single profile data,
            or main.strings.Code.NO and an error message
    """
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        mgm = request.user.profile.management()
        profile = mgm.people.filter(Q(
            Q(is_active=True,
                suspended=False, to_be_zombie=False, is_moderator=False, is_mentor=False,),
            Q(user__email__startswith=query)
            | Q(user__first_name__startswith=query)
            | Q(githubID__startswith=query)
            | Q(nickname__startswith=query)
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
@require_JSON
def removeModerator(request: WSGIRequest):
    """To demote a moderator from the community if possible.
    Manager can only demote the moderators which are in their management and do not have pending moderations
    from outside their management.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.modID (str): The user ID of the moderator to be removed

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if demoted successfully, or main.strings.Code.NO
            and an error message
    """
    try:
        modID = request.POST.get('modID', None)
        if not modID or modID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = request.user.profile.management()
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
                    moderationAssignedAlert(mod)
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
@require_JSON
def addModerator(request: WSGIRequest) -> JsonResponse:
    """To promote a user as moderator in the community, if possible.
    Manager can only promote the people which are in their management.

    Args:
        request (WSGIRequest): The request object
        request.POST.userID (str): The user ID of the user to be promoted

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if promoted successfully,
            or main.strings.Code.NO with an error message
    """
    try:
        userID = request.POST.get('userID', None)
        if not userID or userID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = request.user.profile.management()
        profiles = mgm.people.filter(user__id=userID, is_moderator=False, is_mentor=False,
                                     suspended=False, to_be_zombie=False, is_active=True).values_list('id', flat=True)
        profiles = Profile.objects.filter(
            id__in=list(profiles)).update(is_moderator=True)
        if profiles == 0:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
def mentors(request: WSGIRequest):
    """To render the mentors view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The rendered text/html view
    """
    try:
        mgm = request.user.profile.management()
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
@require_JSON
def searchEligibleMentor(request: WSGIRequest) -> JsonResponse:
    """To search for an eligible user to be a mentor, based on the search query.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.query (str): The search query

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK and a single profile data,
            or main.strings.Code.NO and an error message
    """
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        mgm = request.user.profile.management()
        profile = mgm.people.filter(Q(
            Q(is_active=True,
                suspended=False, to_be_zombie=False, is_mentor=False, is_moderator=False),
            Q(user__email__startswith=query)
            | Q(user__first_name__startswith=query)
            | Q(githubID__startswith=query)
            | Q(nickname__startswith=query)
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
@require_JSON
def removeMentor(request: WSGIRequest):
    """To demote a mentor from the community if possible.
    Manager can only demote the mentors which are in their management and do not have mentorships
    from outside their management.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.mntID (str): The user ID of the mentor to be removed

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if demoted successfully, or main.strings.Code.NO
            and an error message
    """
    try:
        mntID = request.POST.get('mntID', None)
        if not mntID or mntID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = request.user.profile.management()
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
@require_JSON
def addMentor(request: WSGIRequest):
    """To promote a user as mentor in the community, if possible.
    Manager can only promote the people which are in their management.

    Args:
        request (WSGIRequest): The request object
        request.POST.userID (str): The user ID of the user to be promoted

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if promoted successfully,
            or main.strings.Code.NO with an error message
    """
    try:
        userID = request.POST.get('userID', None)
        if not userID or userID == request.user.get_id:
            return respondJson(Code.NO)
        mgm = request.user.profile.management()
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
def labels(request: WSGIRequest):
    """To render the labels index view.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The response text/html view
    """
    return renderer(request, Template.Management.COMMUNITY_LABELS)


@manager_only
@require_GET
def labelType(request: WSGIRequest, type: str):
    """To return the text/html content of labels of a specific type.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Raises:
        Http404: If the label type is invalid

    Returns:
        HttpResponse: The string based response text/html content
    """
    try:
        mgm = request.user.profile.management()
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
        raise ObjectDoesNotExist('Invalid label', type)
    except (ObjectDoesNotExist, AttributeError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_GET
def label(request: WSGIRequest, type: str, labelID: UUID) -> HttpResponse:
    """To render the individual label view.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        type (str): The type of the label
        labelID (UUID): The ID of the label

    Raises:
        Http404: If the label type is invalid

    Returns:
        HttpResponse: The response text/html view
    """
    try:
        data = labelRenderData(request, type, labelID)
        if not data:
            raise ObjectDoesNotExist(type, labelID)
        if type == Code.TOPIC:
            return renderer(request, Template.Management.COMMUNITY_TOPIC, data)
        if type == Code.CATEGORY:
            return renderer(request, Template.Management.COMMUNITY_CATEGORY, data)
        raise ObjectDoesNotExist('Invalid label', type, labelID)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_JSON
def labelCreate(request: WSGIRequest, type: str):
    """To create a new label.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        type (str): The type of the label

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if created successfully,
            or main.strings.Code.NO with an error message
    """
    try:
        name = request.POST['name']
        if type == Code.TOPIC:
            label = addTopicToDatabase(name, request.user.profile)
        elif type == Code.CATEGORY:
            label = addCategoryToDatabase(name, request.user.profile)
        elif type == Code.TAG:
            label = addTagToDatabase(name, request.user.profile)
        else:
            raise ObjectDoesNotExist("invalid label type", type)
        return respondJson(Code.OK, dict(label=dict(id=label.get_id, name=label.name)))
    except (ObjectDoesNotExist, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON
def labelUpdate(request: WSGIRequest, type: str, labelID: UUID):
    """To update an existing label.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        type (str): The type of the label
        labelID (UUID): The ID of the label

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if updated successfully,
            or main.strings.Code.NO with an error message
    """
    try:
        mgm = request.user.profile.management()
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
            raise ObjectDoesNotExist("invalid label type", type, labelID)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON
def labelDelete(request: WSGIRequest, type: str, labelID: UUID):
    """To delete an existing label.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        type (str): The type of the label
        labelID (UUID): The ID of the label

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if deleted successfully,
            or main.strings.Code.NO with an error message
    """
    try:
        mgm = request.user.profile.management()
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
            raise ObjectDoesNotExist("invalid label type", type, labelID)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)

@ratelimit(key='user_or_ip', rate='1/s', block=True, method=(Code.POST,Code.GET))
def contact_categories(request: WSGIRequest) -> JsonResponse:
    """To get the contact categories.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK with list of contact categories (id, name),
            or main.strings.Code.NO with an error message
    """
    try:
        categories = list(ContactCategory.get_all().values("id", "name"))
        return respondJson(Code.OK, dict(categories=categories))
    except (ObjectDoesNotExist, KeyError, ValidationError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@ratelimit(key='user_or_ip', rate='10/m', block=True, method=(Code.POST))
@require_JSON
def contact_subm(request: WSGIRequest) -> JsonResponse:
    """To submit a contact request.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.contactCategoryID (UUID): The ID of the contact category
        request.POST.senderName (str): The name of the sender
        request.POST.senderEmail (str): The email of the sender
        request.POST.senderMessage (str): The contact message of the sender

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK if submitted successfully,
            or main.strings.Code.NO with an error message
    """
    try:
        contactCategoryID = UUID(request.POST['contactCategoryID'])
        contactCategory = ContactCategory.objects.get(id=contactCategoryID)
        senderName = str(request.POST['senderName'])[:100]
        senderEmail = str(request.POST['senderEmail'])[:100]
        validate_email(senderEmail)
        senderMessage = str(request.POST['senderMessage'])[:1000]
        ContactRequest.objects.create(
            contactCategory=contactCategory, senderName=senderName, senderEmail=senderEmail, message=senderMessage)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
def competitions(request: WSGIRequest) -> HttpResponse:
    """To render the management competitions index view.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Raises:
        PermissionDenied: If any exception occurs

    Returns:
        HttpResponse: The response text/html view with context
    """
    try:
        competes = Competition.objects.filter(creator=request.user.profile)
        return renderer(request, Template.Management.COMP_INDEX, dict(competes=competes))
    except Exception as e:
        raise Http404(e)


@manager_only
@require_GET
def competition(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """To render the management competition view.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        compID (UUID): The ID of the competition

    Raises:
        Http404: If the competition does not exist, or any exception occurs

    Returns:
        HttpResponse: The response text/html view with context
    """
    try:
        data = competitionManagementRenderData(request, compID)
        if not data:
            raise ObjectDoesNotExist(compID, request.user)
        return renderer(request, Template.Management.COMP_COMPETE, data)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_JSON
def searchTopic(request: WSGIRequest) -> JsonResponse:
    """To search a topic (primarily for a competition).

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.query (str): The query string

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK with a single topic (id, name),
            or main.strings.Code.NO with an error message
    """
    try:
        query = str(request.POST["query"])
        if not query.strip():
            raise KeyError("query")
        topic = Topic.objects.filter(name__istartswith=query).first()
        return respondJson(Code.OK, dict(topic=dict(
            id=topic.id,
            name=topic.name
        )))
    except KeyError:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON
def searchMentor(request: WSGIRequest) -> JsonResponse:
    """To search a mentor (primarily for a competition).

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.query (str): The query string

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK with a single mentor data
            (id, name, userID, email, url, dp), or main.strings.Code.NO with an error message
    """
    try:
        query = str(request.POST["query"])
        if not query.strip():
            raise KeyError("query")
        excludeIDs = request.POST.get('excludeIDs', [])
        mgm = request.user.profile.management()
        profile = mgm.people.filter(
            Q(
                Q(is_active=True,
                  suspended=False, to_be_zombie=False, is_mentor=True),
                Q(user__email__startswith=query)
                | Q(user__first_name__startswith=query)
                | Q(githubID__startswith=query)
                | Q(nickname__startswith=query)
            )
        ).exclude(user__id__in=excludeIDs).first()
        if profile:
            if not profile.isBlocked(request.user):
                return respondJson(Code.OK, dict(mnt=dict(
                    id=profile.user.id,
                    userID=profile.getUserID(),
                    name=profile.getName(),
                    email=profile.getEmail(),
                    url=profile.getLink(),
                    dp=profile.getDP(),
                )))
        return respondJson(Code.OK)
    except KeyError:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON
def searchModerator(request: WSGIRequest) -> JsonResponse:
    """To search a moderator (primarily for a competition).

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.query (str): The query string

    Returns:
        JsonResponse: The json response object with main.strings.Code.OK with a single moderator data
            (id, name, userID, email, url, dp), or main.strings.Code.NO with an error message
    """
    try:
        query = str(request.POST["query"])
        if not query.strip():
            raise KeyError("query")
        excludeIDs = request.POST.get('excludeIDs', [])
        internalOnly = request.POST.get('internalOnly', True)
        if internalOnly:
            mgm = request.user.profile.management()
            profile = mgm.people.exclude(user__id__in=excludeIDs).filter(
                Q(
                    Q(is_active=True,
                      suspended=False, to_be_zombie=False, is_moderator=True),
                    Q(user__email__startswith=query)
                    | Q(user__first_name__startswith=query)
                    | Q(githubID__startswith=query)
                    | Q(nickname__startswith=query)
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
                    | Q(nickname__startswith=query)
                )
            ).first()
        if profile:
            if not profile.isBlocked(request.user):
                return respondJson(Code.OK, dict(mod=dict(
                    id=profile.user.id,
                    userID=profile.getUserID(),
                    name=profile.getName(),
                    email=profile.getEmail(),
                    url=profile.getLink(),
                    dp=profile.getDP(),
                )))
        return respondJson(Code.OK)
    except KeyError:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
def createCompete(request: WSGIRequest) -> HttpResponse:
    """To render view for creating a competition.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The rendered text/html view with context
    """
    data = dict()
    lastcomp = Competition.objects.filter(creator=request.user.profile).exclude(
        associate__isnull=True).exclude(associate__exact='').order_by("-modifiedOn").first()
    if lastcomp:
        data = dict(associate=lastcomp.get_associate)
    return renderer(request, Template.Management.COMP_CREATE, data)


@manager_only
@require_POST
def submitCompetition(request: WSGIRequest) -> HttpResponse:
    """To submit a competition.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponseRedirect: Redirects to competition management view if successful,
            else to create competition view with error message
    """
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
            raise Exception("Competition not created", compete,
                            request.user.profile, title)
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
    except (ObjectDoesNotExist, KeyError):
        if compete:
            compete.delete()
        return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        if compete:
            compete.delete()
        return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.ERROR_OCCURRED)


@manager_only
@require_JSON
def editCompetition(request: WSGIRequest, compID: UUID) -> JsonResponse:
    """To edit a competition, if possible.
    Edititng of some of the details of a competition depends on its current state.
    For ex. Task of an active competition cannot be edited if there are already submissions present.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        compID (UUID): The competition ID

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if successful,
            or main.strings.Code.NO with error message.
    """
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
@require_JSON
def draftDeleteCompete(request: WSGIRequest, compID: UUID) -> JsonResponse:
    """To convert draft or delete a competition, if possible.
    For ex. Cannot convert an active competition to draft if there are already submissions present.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if successful,
            or main.strings.Code.NO with error message.
    """
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
def reportFeedbacks(request: WSGIRequest) -> HttpResponse:
    """To render reports/feedbacks management view

    METHODS: GET

    Args:
        request (WSGIRequest): The request object

    Returns:
        HttpResponse: The response text/html view
    """
    return renderer(request, Template.Management.REPORTFEED_INDEX)


@ratelimit(key='user_or_ip', rate='15/m', block=True, method=(Code.POST))
@require_JSON
def createReport(request: WSGIRequest) -> JsonResponse:
    """To submit a global report.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if successful,
            or main.strings.Code.NO with error message.
    """
    try:
        email = str(request.POST.get('email', "")[:100]).strip()
        validate_email(email)
        reporter = None
        if email:
            if request.user.is_authenticated and email in request.user.emails():
                reporter = request.user.profile
            else:
                reporter = Profile.objects.filter(
                    user__email__iexact=email).first()
        summary = request.POST['summary'][:1000]
        detail = request.POST.get('detail', '')[:3000]
        report = Report.objects.create(
            reporter=reporter, summary=summary, detail=detail)
        return respondJson(Code.OK, dict(reportID=report.get_id))
    except (KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@ratelimit(key='user_or_ip', rate='15/m', block=True, method=(Code.POST))
@require_JSON
def createFeedback(request: WSGIRequest):
    """To submit a global feedback.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if successful,
            or main.strings.Code.NO with error message.
    """
    try:
        email = str(request.POST.get('email', "")[:100]).strip()
        validate_email(email)
        detail = request.POST["detail"][:3000]
        feedbacker = None
        if email:
            if request.user.is_authenticated and email in request.user.emails():
                feedbacker = request.user.profile
            else:
                feedbacker = Profile.objects.filter(
                    user__email__iexact=email).first()
        feedback = Feedback.objects.create(
            feedbacker=feedbacker, detail=detail)
        return respondJson(Code.OK, data=dict(feedbackID=feedback.get_id))
    except (KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
def reportfeedType(request: WSGIRequest, type: str):
    """To respond with string based text/html content of reports or feedbacks of a specific management.

    NOTE: Feedback is not available for now.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        type (str): The type of section (main.strings.Code.REPORTS)

    Raises:
        Http404: If the type is not valid, or any exception occurs

    Returns:
        HttpResponse: The response string based text/html content with context.
    """
    try:
        mgm = request.user.profile.management()
        if type == Code.REPORTS:
            userreports = ReportedUser.objects.filter(user__id__in=mgm.people.filter(
                suspended=False, is_active=True, to_be_zombie=False).values_list('user__id', flat=True))
            return rendererstr(request, Template.Management.REPORTFEED_REPORTS, dict(reports=[], userreports=userreports))
        # elif type == Code.FEEDBACKS:
        #     feedbacks = Feedback.objects.filter()
        #     return rendererstr(request, Template.Management.REPORTFEED_FEEDBACKS, dict(feedbacks=feedbacks))
        else:
            raise ObjectDoesNotExist(type)
    except (ObjectDoesNotExist, AttributeError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_GET
def reportfeedTypeID(request: WSGIRequest, type: str, ID: UUID):
    """To respond with string based text/html content of a specific report or feedback.

    NOTE: Feedback is not available for now.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        type (str): The type of section (main.strings.Code.REPORTS, main.strings.Code.FEEDBACKS)
        ID (UUID): The id of the report or feedback

    Raises:
        Http404: If the type is not valid, or any exception occurs

    Returns:
        HttpResponse: The response string based text/html content with context.
    """
    try:
        if type == Code.REPORTS:
            report = ReportedUser.objects.get(id=ID)
            return rendererstr(request, Template.Management.REPORTFEED_REPORT, dict(report=report))
        # elif type == Code.FEEDBACKS:
        #     feedback = Feedback.objects.get(id=ID)
        #     return rendererstr(request, Template.Management.REPORTFEED_FEEDBACK, dict(feedback=feedback))
        else:
            raise ObjectDoesNotExist(type)
    except (ObjectDoesNotExist, AttributeError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_JSON
def sendPeopleInvite(request: WSGIRequest) -> JsonResponse:
    """To invite a person to join the management.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if successful,
    """
    try:
        action = request.POST['action']
        if action == Action.CREATE:
            email = request.POST['email'][:100].lower()
            validate_email(email)
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
                    managementInvitationSent(inv)
                else:
                    return respondJson(Code.NO, error=Message.ALREADY_INVITED)
        elif action == Action.REMOVE:
            invID = request.POST['inviteID']
            inv = ManagementInvitation.objects.get(id=invID, resolved=False)
            inv.delete()
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def peopleMGMInvitation(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To render invitation view for maanagement invited user.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The id of the invitation

    Raises:
        Http404: If the invitation does not exist or is invalid

    Returns:
        HttpResponse: The response text/html view with context.
    """
    try:
        invitation = ManagementInvitation.objects.get(id=inviteID,
                                                      receiver=request.user.profile, expiresOn__gt=timezone.now(),
                                                      resolved=False,
                                                      management__profile__suspended=False,
                                                      management__profile__is_active=True
                                                      )
        return renderer(request, Template.Management.INVITATION,
                        dict(invitation=invitation))
    except (ObjectDoesNotExist, ValidationError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def peopleMGMInvitationAction(request: WSGIRequest, inviteID: UUID) -> HttpResponse:
    """To take action on management invitation by the invited user.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        inviteID (UUID): The id of the invitation

    Raises:
        Http404: If the invitation does not exist or is invalid

    Returns:
        HttpResponseRedirect: If the invitation is resolved, redirect to the management profile view.
            else, redirect to the invitation view with error.
    """
    invitation = None
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
        else:
            raise ObjectDoesNotExist(action, inviteID)
        if not done:
            return redirect(invitation.getLink(error=Message.ERROR_OCCURRED))
        if accept:
            message = Message.JOINED_MANAGEMENT
            managementInvitationAccepted(invitation)
        else:
            message = Message.DECLINED_JOIN_MANAGEMENT
        return redirect(invitation.management.getLink(message=message))
    except (ObjectDoesNotExist, KeyError, ValidationError) as o:
        if invitation:
            return redirect(invitation.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if invitation:
            return redirect(invitation.getLink(error=Message.INVALID_REQUEST))
        raise Http404(e)


@normal_profile_required
@require_JSON
def peopleMGMRemove(request: WSGIRequest) -> JsonResponse:
    """To remove a person from the management, by the manager or the person themselves.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        request.POST.userID (UUID): The id of the user to be removed
        request.POST.mgmID (UUID): The id of the management from which the person is to be removed

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if successful,
            or with main.strings.Code.NO if not successful.
    """
    try:
        userID = UUID(request.POST['userID'])
        mgmID = UUID(request.POST['mgmID'])

        person = Profile.objects.get(user__id=userID)
        mgm = Management.objects.get(id=mgmID)

        if not (request.user.profile == person or request.user.profile == mgm.profile):
            raise ObjectDoesNotExist(mgm, person)
        if person.is_moderator:
            if Moderation.objects.filter(competition__creator=mgm.profile, moderator=person, resolved=False).exists():
                return respondJson(Code.NO, error=Message.PENDING_MODERATIONS_EXIST)

        if not person.removeFromManagement(mgm.id):
            raise Exception("Failed to remove from management", mgm, person)
        managementPersonRemoved(mgm, person)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
