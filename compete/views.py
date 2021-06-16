from django.http.response import Http404, HttpResponse
from .methods import renderer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from main.strings import code
from .models import *
from .methods import getCompetitionSectionHTML


@require_GET
def index(request):
    try:
        actives = Competition.objects.filter(active=True)
    except:
        actives = None
    try:
        inactives = Competition.objects.filter(active=False)
    except:
        inactives = None

    return renderer(request, 'index.html', {"actives": actives, "inactives": inactives})


@require_GET
def competition(request, compID):
    try:
        compete = Competition.objects.get(id=compID)
        return renderer(request, 'profile.html', {"compete": compete})
    except:
        raise Http404()


@require_GET
def competitionTab(request,compID, section):
    print('here')
    try:
        compete = Competition.objects.get(id=compID)
        data = getCompetitionSectionHTML(compete,section,request)
        if data:
            return HttpResponse(data)
        else:
            raise Http404()
    except:
        raise Http404()

@login_required
@require_POST
def createSubmission(request, compID):
    """
    Take participation
    """
    try:
        competition = Competition.objects.get(id=compID, active=True)
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
    """
    Already existing participation submission
    """
    try:
        competition = Competition.objects.get(id=compID, active=True)
        submission = Submission.objects.get(
            id=submitID, competition=competition, members=request.user)
        submission.submitOn = timezone.now()
        submission.submitted = True
        submission.save()
        return HttpResponse(code.OK)
    except:
        return HttpResponse(code.SUBMISSION_ERROR)
