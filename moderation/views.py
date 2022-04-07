from uuid import UUID

from compete.mailers import submissionsModeratedAlert
from compete.models import Submission
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from main.decorators import (decode_JSON, moderator_only,
                             normal_profile_required, require_JSON_body)
from main.methods import errorLog, respondJson, user_device_notify
from main.strings import COMPETE, CORE_PROJECT, PEOPLE, PROJECTS, Code, Message
from management.models import ReportCategory
from people.models import ProfileTopic
from projects.mailers import projectRejectedNotification
from projects.methods import setupApprovedCoreProject, setupApprovedProject
from projects.models import (CoreProjectVerificationRequest,
                             FreeProjectVerificationRequest)

from .apps import APPNAME
from .mailers import moderationAssignedAlert
from .methods import (getModeratorToAssignModeration, moderationRenderData,
                      renderer, requestModerationForCoreProject,
                      requestModerationForObject)
from .models import Moderation
from .receivers import *


@normal_profile_required
@require_GET
def moderation(request: WSGIRequest, id: UUID) -> HttpResponse:
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
    """
    Message by moderator or requestor.
    """
    try:
        now = timezone.now()
        responseData = str(request.POST.get('responsedata', "")).strip()
        requestData = str(request.POST.get('requestdata', "")).strip()
        if not responseData and not requestData:
            raise Exception()

        mod = Moderation.objects.get(id=modID)
        if mod.resolved:
            return redirect(mod.getLink(alert=Message.ALREADY_RESOLVED))
        if mod.is_stale:
            raise Exception()

        isRequester = mod.isRequestor(request.user.profile)
        isModerator = mod.moderator == request.user.profile
        if not isRequester and not isModerator:
            raise Exception()

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
            raise Exception()
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        raise Http404(e)


@moderator_only
@require_JSON_body
def action(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """
    Moderator action on moderation. (Project, primarily)
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    mod = None
    try:
        mod = Moderation.objects.get(
            id=modID, moderator=request.user.profile, resolved=False)
        if mod.is_stale:
            raise Exception()
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
    except ObjectDoesNotExist as o:
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
def reapply(request: WSGIRequest, modID: UUID) -> HttpResponse:
    """
    Re-request for moderation if possible, and if rejected or stale. (Project, primarily)
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
@require_JSON_body
def approveCompetition(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """
    To finalize valid submissions for judgement of a competition under moderation.
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
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


def reportCategories(request: WSGIRequest):
    try:
        categories = ReportCategory.objects.all()
        reports = []
        for cat in categories:
            reports.append(dict(id=cat.id, name=cat.name))
        return respondJson(Code.OK, dict(reports=reports))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@normal_profile_required
@require_JSON_body
def reportModeration(request: WSGIRequest):
    try:
        report = request.POST['report']
        moderationID = request.POST['moderationID']
        moderation = Moderation.objects.get(id=moderationID)
        category = ReportCategory.objects.get(id=report)
        request.user.profile.reportModeration(moderation, category)
        return respondJson(Code.OK)
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
