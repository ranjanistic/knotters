from django.http.response import Http404, HttpResponse, JsonResponse
from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from compete.models import Submission
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone
from projects.methods import setupApprovedProject
from main.methods import respondJson
from main.strings import Code, Message, PROJECTS, PEOPLE, COMPETE
from main.decorators import require_JSON_body
from .decorators import moderator_only
from .models import Moderation
from .methods import renderer, requestModerationForObject


@require_GET
@login_required
def moderation(request: WSGIRequest, id: UUID) -> HttpResponse:
    try:
        moderation = Moderation.objects.get(id=id)
        isModerator = moderation.moderator == request.user.profile
        isRequestor = moderation.isRequestor(request.user.profile)
        if not isRequestor and not isModerator:
            raise Exception()
        data = {'moderation': moderation, 'ismoderator': isModerator}

        if moderation.type == COMPETE:
            if isRequestor:
                data['allSubmissionsMarkedByJudge'] = moderation.competition.allSubmissionsMarkedByJudge(
                    request.user.profile)
        return renderer(request, moderation.type, data)
    except:
        raise Http404()


@require_POST
@login_required
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


@require_JSON_body
@moderator_only
def action(request: WSGIRequest, modID: UUID) -> JsonResponse:
    """
    Moderator action on moderation. (Project, primarily)
    """
    try:
        approve = request.POST.get('approve', '')

        mod = Moderation.objects.get(
            id=modID, moderator=request.user.profile, resolved=False)
        if not approve:
            done = mod.reject()
            return respondJson(Code.OK if done else Code.NO)
        elif approve:
            done = mod.approve()
            if done:
                done = setupApprovedProject(mod.project, mod.moderator)
            return respondJson(Code.OK if done else Code.NO)
        else:
            return respondJson(Code.NO, error=Message.INVALID_RESPONSE)
    except Exception as e:
        print(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@require_POST
@login_required
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
            raise Exception()
        if not newmod:
            raise Exception()
        else:
            return redirect(newmod.getLink(alert=Message.MODERATION_REAPPLIED))
    except:
        raise Http404()


@require_JSON_body
@moderator_only
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
