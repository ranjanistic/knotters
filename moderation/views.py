from uuid import UUID

from compete.mailers import submissionsModeratedAlert
from compete.models import Submission
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from main.decorators import (decode_JSON, moderator_only,
                             normal_profile_required, require_JSON)
from main.methods import errorLog, respondJson, user_device_notify
from main.strings import COMPETE, CORE_PROJECT, PEOPLE, PROJECTS, Code, Message
from management.models import ReportCategory
from people.models import ProfileTopic
from projects.mailers import projectRejectedNotification
from projects.methods import setupApprovedCoreProject, setupApprovedProject
from projects.models import (CoreProjectVerificationRequest,
                             FreeProjectVerificationRequest)
from ratelimit.decorators import ratelimit

from .mailers import moderationAssignedAlert
from .methods import (getModeratorToAssignModeration, moderationRenderData,
                      renderer, requestModerationForCoreProject,
                      requestModerationForObject)
from .models import Moderation
from .receivers import *


@normal_profile_required
@require_GET
def moderation(request: WSGIRequest, id: UUID) -> HttpResponse:
    """Renders a moderation view.

    Args:
        request (WSGIRequest): The request object.
        id (UUID): The id of the moderation.

    Raises:
        Http404: If the moderation does not exist, or any exception occurs.

    Returns:
        HttpResponse: The rendered text/html view with context.
    """
    try:
        data = moderationRenderData(request, id)
        if not data:
            raise ObjectDoesNotExist(id)
        return renderer(request, data["moderation"].type, data)
    except (ObjectDoesNotExist, KeyError) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
def message(request: WSGIRequest, modID: UUID) -> HttpResponse:
    """To save message by moderator or requestor in an active moderation.

    Args:
        request (WSGIRequest): The request object.
        modID (UUID): The id of the moderation.

    Raises:
        Http404: If the moderation does not exist, or any exception occurs.

    Returns:
        HttpResponseRedirect: The redirect to the moderation view.
    """
    mod = None
    try:
        now = timezone.now()
        responseData = str(request.POST.get('responsedata', "")).strip()
        requestData = str(request.POST.get('requestdata', "")).strip()
        if not responseData and not requestData:
            raise ObjectDoesNotExist(modID)

        mod = Moderation.objects.get(id=modID, resoved=False)

        if mod.is_stale:
            raise ObjectDoesNotExist(mod)

        isRequester = mod.isRequestor(request.user.profile)
        isModerator = mod.moderator == request.user.profile

        if isModerator:
            if not responseData:
                raise Exception()
            if mod.response != responseData:
                mod.response = responseData
                mod.respondOn = now
                user_device_notify(mod.requestor.user, f"Moderation Response Update",
                                   f"Moderator said: {responseData}", url=mod.getLink(), image=mod.getImageByType())
                mod.save()
            return redirect(mod.getLink(alert=Message.RES_MESSAGE_SAVED))
        elif isRequester:
            if not requestData:
                raise Exception()
            if mod.request != requestData:
                mod.request = requestData
                user_device_notify(mod.requestor.user, f"Moderation Response Update",
                                   f"Requestor said: {requestData}", url=mod.getLink(), image=mod.getImageByType())
                mod.save()
            return redirect(mod.getLink(alert=Message.REQ_MESSAGE_SAVED))
        else:
            raise ObjectDoesNotExist(request.user)
    except (ObjectDoesNotExist, ValidationError) as o:
        if mod:
            redirect(mod.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if mod:
            redirect(mod.getLink(error=Message.ERROR_OCCURRED))
        raise Http404(e)


@moderator_only
@require_JSON
def action(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """To take action on moderation, to be used by moderators for verified  or core project primarily.

    Args:
        request (WSGIRequest): The request object.
        modID (UUID): The id of the moderation.

    Raises:
        Http404: If the moderation does not exist, or any exception occurs.

    Returns:
        JsonResponse: The json response main.strings.Code.OK or main.strings.Code.NO.
        HttpResponseRedirect: The redirect to the moderation view or relevant view depending upon action status.
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    mod = None
    try:
        mod = Moderation.objects.get(
            id=modID, moderator=request.user.profile, resolved=False)
        if mod.is_stale:
            raise ObjectDoesNotExist(mod)
        skip = request.POST.get('skip', None)
        if skip:
            if mod.type == CORE_PROJECT or mod.type == COMPETE:
                return redirect(mod.getLink(error=Message.INVALID_REQUEST))
            onlyModProfiles = None
            if mod.internal_mod and mod.requestor.is_manager():
                onlyModProfiles = mod.requestor.management(
                ).moderators().exclude(id=mod.moderator.id)
                if not len(onlyModProfiles):
                    return redirect(mod.getLink(error=Message.NO_MODERATORS_AVAILABLE))

            newmod = getModeratorToAssignModeration(
                type=mod.type, object=mod.object, ignoreModProfiles=[mod.moderator], onlyModProfiles=onlyModProfiles)
            if not newmod:
                return redirect(mod.getLink(error=Message.NO_MODERATORS_AVAILABLE))
            mod.moderator = newmod
            mod.save()
            moderationAssignedAlert(mod)
            return redirect(request.user.profile.getLink(alert=Message.MODERATION_SKIPPED))
        else:
            approve = request.POST.get('approve', None)
            if approve == None:
                return respondJson(Code.NO)
            if not approve:
                done = mod.reject()
                if done and mod.type == PROJECTS:
                    if FreeProjectVerificationRequest.objects.filter(verifiedproject=mod.project, resolved=False).exists():
                        done = (FreeProjectVerificationRequest.objects.get(
                            verifiedproject=mod.project, resolved=False)).decline()
                    elif CoreProjectVerificationRequest.objects.filter(verifiedproject=mod.project, resolved=False).exists():
                        done = (CoreProjectVerificationRequest.objects.get(
                            verifiedproject=mod.project, resolved=False)).decline()
                    projectRejectedNotification(mod.project)
                if done and mod.type == CORE_PROJECT:
                    projectRejectedNotification(mod.coreproject)
                return respondJson(Code.OK if done else Code.NO)
            elif approve:
                done = mod.approve()
                if done:
                    if mod.type == PROJECTS:
                        if FreeProjectVerificationRequest.objects.filter(verifiedproject=mod.project, resolved=False).exists():
                            done = (FreeProjectVerificationRequest.objects.get(
                                verifiedproject=mod.project, resolved=False)).accept()
                            if done:
                                done = setupApprovedProject(
                                    mod.project, mod.moderator)
                        elif CoreProjectVerificationRequest.objects.filter(verifiedproject=mod.project, resolved=False).exists():
                            done = (CoreProjectVerificationRequest.objects.get(
                                verifiedproject=mod.project, resolved=False)).accept()
                        else:
                            done = setupApprovedProject(
                                mod.project, mod.moderator)
                        if not done:
                            mod.revertApproval()
                    elif mod.type == CORE_PROJECT:
                        done = setupApprovedCoreProject(
                            mod.coreproject, mod.moderator)
                        if not done:
                            mod.revertApproval()

                return respondJson(Code.OK if done else Code.NO, error=Message.ERROR_OCCURRED if not done else str())
            else:
                return respondJson(Code.NO, error=Message.INVALID_RESPONSE)
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if mod:
            return redirect(mod.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if mod:
            return redirect(mod.getLink(error=Message.ERROR_OCCURRED))
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@decode_JSON
def reapply(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """To re-request for moderation, if rejected or stale, if possible (Verified or Core Projects, primarily),
    to be used by requestor via POST method.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.
        modID (UUID): The id of the moderation.

    Raises:
        Http404: If the moderation does not exist, or any exception occurs.

    Returns:
        JsonResponse: The json response main.strings.Code.OK or main.strings.Code.NO.
        HttpResponseRedirect: The redirect to the moderation view or relevant view depending upon reapplication status.
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        mod = Moderation.objects.get(
            id=modID)
        newmod = None
        if mod.type == PROJECTS:
            if (mod.resolved and mod.status == Code.REJECTED) or mod.is_stale:
                if mod.is_stale:
                    mod.moderator.decreaseXP(by=2)
                newmod = requestModerationForObject(
                    mod.project, mod.type, reassignIfRejected=True, stale_days=mod.stale_days, useInternalMods=mod.internal_mod)
        elif mod.type == PEOPLE:
            newmod = requestModerationForObject(
                mod.profile, mod.type, reassignIfRejected=True, stale_days=mod.stale_days, useInternalMods=mod.internal_mod)
        elif mod.type == COMPETE:
            newmod = requestModerationForObject(
                mod.competition, mod.type, reassignIfRejected=True, stale_days=mod.stale_days, useInternalMods=mod.internal_mod)
        elif mod.type == CORE_PROJECT and mod.is_stale:
            mod.moderator.decreaseXP(by=2)
            newmod = requestModerationForCoreProject(
                mod.coreproject, stale_days=mod.stale_days, useInternalMods=mod.internal_mod)
        else:
            return redirect(mod.getLink(alert=Message.INVALID_REQUEST))
        if not newmod:
            return redirect(mod.getLink(alert=Message.ERROR_OCCURRED))
        else:
            return redirect(newmod.getLink(alert=Message.MODERATION_REAPPLIED))
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@moderator_only
@require_JSON
def approveCompetition(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """To finalize valid submissions to be sent for judgement of a competition under moderation (For Competitions).

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.
        modID (UUID): The id of the moderation.

    Raises:
        Http404: If the moderation does not exist, or any exception occurs.

    Returns:
        JsonResponse: The json response main.strings.Code.OK or main.strings.Code.NO.
    """
    try:
        mod = Moderation.objects.get(
            id=modID, type=COMPETE, status=Code.MODERATION, resolved=False, moderator=request.user.profile)
        submissions = request.POST['submissions']
        invalidSubIDs = []
        for sub in submissions:
            if not sub['valid']:
                invalidSubIDs.append(sub['subID'])
        competition = mod.competition
        Submission.objects.filter(
            competition=competition, id__in=invalidSubIDs).update(valid=False)
        mod.status = Code.APPROVED
        mod.resolved = True
        mod.save()
        submissionsModeratedAlert(competition)

        totalsubs = competition.totalSubmissions()
        topics = competition.getTopics()

        modXP = (totalsubs//(len(topics)+1))//2
        for topic in topics:
            profiletopic, created = ProfileTopic.objects.get_or_create(
                profile=request.user.profile,
                topic=topic,
                defaults=dict(
                    profile=request.user.profile,
                    topic=topic,
                    trashed=True,
                    points=modXP
                )
            )
            if not created:
                profiletopic.increasePoints(by=modXP)
        request.user.profile.increaseXP(by=modXP)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@ratelimit(key='user_or_ip', rate='1/s', block=True, method=(Code.POST, Code.GET))
def reportCategories(request: WSGIRequest) -> JsonResponse:
    """To get the categories to be used for reporting.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: The json response main.strings.Code.OK with report categories (id, name), or main.strings.Code.NO.
    """
    try:
        reports = list(ReportCategory.get_all().values_list("id", "name"))
        return respondJson(Code.OK, dict(reports=reports))
    except (ObjectDoesNotExist, ValidationError, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def reportModeration(request: WSGIRequest) -> JsonResponse:
    """To report a moderation.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        JsonResponse: The json response main.strings.Code.OK or main.strings.Code.NO.
    """
    try:
        report = UUID(request.POST['report'][:20])
        moderationID = UUID(request.POST['moderationID'][:20])
        moderation = Moderation.objects.get(id=moderationID)
        category = ReportCategory.get_cache_one(id=report)
        request.user.profile.reportModeration(moderation, category)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
