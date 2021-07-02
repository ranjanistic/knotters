from django.http.response import Http404, HttpResponse, JsonResponse
import uuid
from django.http.request import HttpRequest
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone
from projects.methods import setupApprovedProject
from main.strings import code, PROJECTS, PEOPLE, COMPETE
from main.decorators import require_JSON_body
from .decorators import moderator_only
from .models import Moderation
from .methods import renderer, requestModerationForObject


@require_GET
@login_required
def moderation(request: HttpRequest, id: uuid) -> HttpResponse:
    try:
        moderation = Moderation.objects.get(id=id)
        isModerator = moderation.moderator == request.user.profile
        if not moderation.isRequestor(request.user.profile) and not isModerator:
            raise Exception()
        return renderer(request, moderation.type, {'moderation': moderation, 'ismoderator': isModerator})
    except:
        raise Http404()


@require_POST
@login_required
def message(request: HttpRequest, modID: uuid) -> HttpResponse:
    """
    Message by moderator or requestor.
    """
    try:
        responseData = str(request.POST.get('responsedata', "")).strip()
        requestData = str(request.POST.get('requestdata', "")).strip()
        if not responseData and not requestData:
            raise Exception()

        mod = Moderation.objects.get(id=modID)
        if mod.resolved:
            raise redirect(mod.getLink(alert="Already resolved"))
        isRequester = mod.isRequestor(request.user.profile)
        isModerator = mod.moderator == request.user.profile
        if not isRequester and not isModerator:
            raise Exception()

        if isModerator:
            if not responseData:
                raise Exception()
            if mod.response != responseData:
                mod.response = responseData
                mod.respondOn = timezone.now()
                mod.save()
            return redirect(mod.getLink(alert="Response saved"))
        elif isRequester:
            if not requestData:
                raise Exception()
            if mod.request != requestData:
                mod.request = requestData
                mod.save()
            return redirect(mod.getLink(alert="Message saved"))
        else:
            raise Exception()
    except:
        raise Http404()


@require_POST
@require_JSON_body
@login_required
@moderator_only
def action(request: HttpRequest, modID: uuid) -> HttpResponse:
    """
    Moderator action on moderation.
    """
    try:
        approve = request.POST.get('approve', '')
        mod = Moderation.objects.get(
            id=modID, moderator=request.user.profile, resolved=False)
        if not approve:
            done = mod.reject()
            return JsonResponse({'code': code.OK if done else code.NO})
        elif approve:
            done = mod.approve()
            if done:
                done = setupApprovedProject(mod.project, mod.moderator)
            return JsonResponse({'code': code.OK if done else code.NO})
        else:
            return JsonResponse({'code': code.NO, 'error': "Invalid response"})
    except:
        return JsonResponse({'code': code.NO, 'error': "Invalid response"})


@require_POST
@login_required
def reapply(request: HttpRequest, modID: uuid) -> HttpResponse:
    """
    Re-request for moderation if possible, and if previous one rejected.
    """
    try:
        mod = Moderation.objects.get(id=modID, resolved=True, status=code.REJECTED)
        if mod.type == PROJECTS:
            newmod = requestModerationForObject(mod.project, mod.type,reassignIfRejected=True)
        elif mod.type == PEOPLE:
            newmod = requestModerationForObject(mod.profile, mod.type,reassignIfRejected=True)
        elif mod.type == COMPETE:
            newmod = requestModerationForObject(mod.competition, mod.type,reassignIfRejected=True)
        else:
            raise Exception()
        if not newmod:
            raise Exception()
        else:
            return redirect(newmod.getLink(alert="Re-applied for moderation to another moderator."))
    except:
        raise Http404()
