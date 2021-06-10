from django.http.response import Http404, HttpResponse
from .methods import renderer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from .models import *
from main.strings import code
from django.utils import timezone

@require_GET
def index(request):
    return renderer(request, 'home.html')


@require_GET
def competition(request, compID):
    return renderer(request, 'competition.html', {"compID": compID })


@login_required
@require_POST
def createSubmission(request, compID):
    try:
        competition = Competition.objects.get(id=compID,active=True)
        try:
            Submission.objects.filter(
                competition=competition, members=request.user)
            return HttpResponse(code.SUBMISSION_EXISTS)
        except:
            return HttpResponse(code.NO)
            # newSubmission = Submission.objects.create(
            #     competition=competition, members=request.user)
    except:
        return HttpResponse(code.SUBMISSION_ERROR)


@login_required
@require_POST
def finalSubmit(request, compID, submitID):
    try:
        competition = Competition.objects.get(id=compID,active=True)
        submission = Submission.objects.get(id=submitID,competition=competition, members=request.user)
        submission.submitOn = timezone.now()
        submission.submitted = True
        submission.save()
        return HttpResponse(code.OK)
    except:
        return HttpResponse(code.SUBMISSION_ERROR)
