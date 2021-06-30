from moderation.decorators import moderator_only
from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from people.models import User
from projects.models import Project
from projects.methods import setupApprovedProject
from compete.models import Competition
from main.strings import PROJECTS, PEOPLE, COMPETE, code
from .models import *
from .methods import renderer

@require_GET
@login_required
def moderation(request,id):
    try:
        moderation = Moderation.objects.get(id=id)
        if moderation.resolved: raise Exception()
        if not moderation.isRequestor(request.user.profile) and moderation.moderator != request.user.profile:
            raise Exception()

        return renderer(request, moderation.type, {'moderation':moderation, 'ismoderator': moderation.moderator == request.user.profile })
    except:
        raise Http404()


@require_POST
@login_required
@moderator_only
def disapprove(request):
    try:
        id = request.POST["id"]
        reason = request.POST["reason"]
        obj = Moderation.objects.get(id=id,moderator=request.user)
        obj.reject(reason)
        return HttpResponse(code.OK)
    except:
        return HttpResponse(code.NO)

@require_POST
@login_required
@moderator_only
def approve(request):
    try:
        id = request.POST["id"]
        reason = str(request.POST["reason"]).strip()
        obj = Moderation.objects.get(id=id,moderator=request.user.profile)
        obj.approve(reason)
        if obj.type == PROJECTS:
            done = setupApprovedProject(obj.project,obj.moderator)
            if not done:
                return HttpResponse(code.NO)
        return HttpResponse(code.OK)
    except:
        return HttpResponse(code.NO)
