from moderation.decorators import moderator_only
from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth.decorators import login_required
from people.models import User
from project.models import Project
from project.methods import setupNewProject
from compete.models import Competition
from main.strings import PROJECT, PEOPLE, COMPETE, code
from .models import *
from .methods import renderer

@require_GET
def moderation(request, division, id):
    try:
        if not [PEOPLE, PROJECT, COMPETE].__contains__(division):
            raise Http404()
        else:
            data = {}
            moderation = None
            if division == PEOPLE:
                user = User.objects.get(id=id)
                moderation = Moderation.objects.get(user=user)
                data = {'person': user}
            elif division == PROJECT:
                project = Project.objects.get(id=id)
                moderation = Moderation.objects.get(project=project)
                data = {'project': project}
            elif division == COMPETE:
                competition = Competition.objects.get(id=id)
                moderation = Moderation.objects.get(competition=competition)
                data = {'competition': competition}
            data['moderation'] = moderation
            return renderer(request, f'{division}.html', data)
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
        reason = request.POST["reason"]
        obj = Moderation.objects.get(id=id,moderator=request.user)
        obj.approve(reason)
        if obj.type == PROJECT:
            done = setupNewProject(obj.project,obj.moderator)
            if not done:
                return HttpResponse(code.NO)
        return HttpResponse(code.OK)
    except:
        return HttpResponse(code.NO)
