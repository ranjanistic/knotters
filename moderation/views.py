from django.http.response import Http404, HttpResponse, JsonResponse
from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from compete.models import Submission
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import redirect
from django.utils import timezone
from projects.methods import setupApprovedProject
from projects.mailers import projectRejectedNotification
from main.methods import errorLog, respondJson, respondRedirect
from main.strings import Code, Message, PROJECTS, PEOPLE, COMPETE, URL
from main.decorators import require_JSON_body, moderator_only, normal_profile_required
from .apps import APPNAME
from .mailers import moderationAssignedAlert
from .models import Moderation
from .methods import getModeratorToAssignModeration, renderer, requestModerationForObject


@normal_profile_required
@require_GET
def moderation(request: WSGIRequest, id: UUID) -> HttpResponse:
    try:
        moderation = Moderation.objects.get(id=id)
        isModerator = moderation.moderator == request.user.profile
        isRequestor = moderation.isRequestor(request.user.profile)
        if not isRequestor and not isModerator:
            raise Exception()
        data = dict(moderation=moderation,ismoderator=isModerator)
        if moderation.type == COMPETE:
            if isRequestor:
                data = dict(**data, allSubmissionsMarkedByJudge=moderation.competition.allSubmissionsMarkedByJudge(request.user.profile))
        if moderation.type == PROJECTS and moderation.resolved:
            forwarded = Moderation.objects.filter(~Q(id=id),type=PROJECTS,project=moderation.project,resolved=False).order_by('-requestOn').first()
            data = dict(**data,forwarded=forwarded)
        return renderer(request, moderation.type, data)
    except:
        raise Http404()


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
            raise redirect(mod.getLink(alert=Message.ALREADY_RESOLVED))
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
                mod.save()
            return redirect(mod.getLink(alert=Message.RES_MESSAGE_SAVED))
        elif isRequester:
            if not requestData:
                raise Exception()
            if mod.request != requestData:
                mod.request = requestData
                mod.save()
            return redirect(mod.getLink(alert=Message.REQ_MESSAGE_SAVED))
        else:
            raise Exception()
    except:
        raise Http404()


@moderator_only
@require_JSON_body
def action(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """
    Moderator action on moderation. (Project, primarily)
    """
    try:
        mod = Moderation.objects.get(id=modID, moderator=request.user.profile, resolved=False)
        skip = request.POST.get('skip', None)
        if skip:
            newmod = getModeratorToAssignModeration(mod.type,mod.object,[mod.moderator])
            mod.moderator = newmod
            mod.save()
            moderationAssignedAlert(mod)
            return respondRedirect(PEOPLE,'',alert=Message.MODERATION_SKIPPED)
        else:
            approve = request.POST.get('approve', None)
            if approve == None:
                return respondJson(Code.NO)
            if not approve:
                done = mod.reject()
                if done and mod.type == PROJECTS:
                    projectRejectedNotification(mod.project)
                return respondJson(Code.OK if done else Code.NO)
            elif approve:
                done = mod.approve()
                if done and mod.type == PROJECTS:
                    done = setupApprovedProject(mod.project, mod.moderator)
                    if not done:
                        mod.revertApproval()
                return respondJson(Code.OK if done else Code.NO, error=Message.ERROR_OCCURRED if not done else str())
            else:
                return respondJson(Code.NO, error=Message.INVALID_RESPONSE)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
def reapply(request: WSGIRequest, modID: UUID) -> HttpResponse:
    """
    Re-request for moderation if possible, and if previous one rejected. (Project, primarily)
    """
    try:
        mod = Moderation.objects.get(
            id=modID, resolved=True, status=Code.REJECTED)
        if mod.type == PROJECTS:
            newmod = requestModerationForObject(
                mod.project, mod.type, reassignIfRejected=True)
        elif mod.type == PEOPLE:
            newmod = requestModerationForObject(
                mod.profile, mod.type, reassignIfRejected=True)
        elif mod.type == COMPETE:
            newmod = requestModerationForObject(
                mod.competition, mod.type, reassignIfRejected=True)
        else:
            return redirect(mod.getLink(alert=Message.ERROR_OCCURRED))
        if not newmod:
            return redirect(mod.getLink(alert=Message.ERROR_OCCURRED))
        else:
            return redirect(newmod.getLink(alert=Message.MODERATION_REAPPLIED))
    except:
        raise Http404()


@moderator_only
@require_JSON_body
def approveCompetition(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """
    To finalize valid submissions for judgement of a competition under moderation.
    """
    try:
        submissions = request.POST['submissions']
        invalidSubIDs = []
        for sub in submissions:
            if not sub['valid']:
                invalidSubIDs.append(sub['subID'])
        Submission.objects.filter(id__in=invalidSubIDs).update(valid=False)
        Moderation.objects.filter(id=modID, type=COMPETE, status=Code.MODERATION, resolved=False).update(
            status=Code.APPROVED, resolved=True)
        return respondJson(Code.OK)
    except:
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
