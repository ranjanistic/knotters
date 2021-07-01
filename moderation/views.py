from django.http.response import Http404, JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone
from projects.methods import setupApprovedProject
from main.strings import code, PROJECTS, PEOPLE, COMPETE
from main.decorators import require_JSON_body
from .decorators import moderator_only
from .models import Moderation
from .methods import renderer, requestModeration

@require_GET
@login_required
def moderation(request,id):
    try:
        moderation = Moderation.objects.get(id=id)
        isModerator = moderation.moderator == request.user.profile
        if not moderation.isRequestor(request.user.profile) and not isModerator:
            raise Exception()
        return renderer(request, moderation.type, {'moderation':moderation, 'ismoderator': isModerator })
    except:
        raise Http404()

@require_POST
@login_required
def message(request,modID):
    try:
        responseData = str(request.POST.get('responsedata',"")).strip()
        requestData = str(request.POST.get('requestdata',"")).strip()
        if not responseData and not requestData: raise Exception()

        mod = Moderation.objects.get(id=modID)
        if mod.resolved: raise Exception()
        isRequester = mod.isRequestor(request.user.profile)
        isModerator = mod.moderator == request.user.profile
        if not isRequester and not isModerator:
            raise Exception()

        if isModerator:
            if not responseData: raise Exception()
            if mod.response != responseData:
                mod.response = responseData
                mod.respondOn = timezone.now()
                mod.save()
            return redirect(mod.getLink(alert="Response saved"))
        elif isRequester:
            if not requestData: raise Exception()
            if mod.request != requestData:
                mod.request = requestData
                mod.save()
            return redirect(mod.getLink(alert="Message saved"))
        else: raise Exception()
    except:
        raise Http404()

@require_POST
@require_JSON_body
@login_required
@moderator_only
def action(request,modID):
    try:
        approve = request.POST.get('approve','')
        mod = Moderation.objects.get(id=modID,moderator=request.user.profile,resolved=False)
        if not approve:
            done = mod.reject()
            return JsonResponse({ 'code': code.OK if done else code.NO })
        elif approve:
            done = mod.approve()
            if done: 
                done = setupApprovedProject(mod.project,mod.moderator)
            return JsonResponse({ 'code': code.OK if done else code.NO })
        else: return JsonResponse({'code':code.NO, 'error': "Invalid response"})
    except:
        return JsonResponse({'code':code.NO, 'error': "Invalid response"})

@require_POST
@login_required
def reapply(request, modID):
    try:
        mod = Moderation.objects.get(id=modID,resolved=True,status=code.REJECTED,retries__gt=0)
        if mod.type == PROJECTS:
            requested = requestModeration(mod.project,mod.type)
        elif mod.type == PEOPLE:
            requested = requestModeration(mod.profile,mod.type)
        elif mod.type == COMPETE:
            requested = requestModeration(mod.competition,mod.type)
        else:
            raise Exception()

        if not requested: raise Exception()
        else: return redirect(mod.getLink(alert="Re-applied for moderation to another moderator."))
    except:
        raise Http404()