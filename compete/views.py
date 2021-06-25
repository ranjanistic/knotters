from main.methods import renderData
from django.db.models import Q
from django.http.response import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect,render
from people.models import User
from .methods import renderer, sendParticipationWelcomeMail
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from main.strings import code
from .models import *
from .methods import getCompetitionSectionHTML, getIndexSectionHTML,sendParticipantInvitationMail, sendSubmissionConfirmedMail


@require_GET
def index(request):
    return renderer(request, 'index')


@require_GET
def indexTab(request, tab):
    try:
        data = getIndexSectionHTML(section=tab, request=request)
        if data:
            return HttpResponse(data)
        else:
            raise Http404()
    except:
        raise Http404()


@require_GET
def competition(request, compID):
    try:
        compete = Competition.objects.get(id=compID)
        return renderer(request, 'profile', {"compete": compete})
    except:
        raise Http404()

@require_GET
def competitionTab(request, compID, section):
    print('here')
    try:
        compete = Competition.objects.get(id=compID)
        data = getCompetitionSectionHTML(compete, section, request)
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
        competition = Competition.objects.get(id=compID)
        if not competition.isActive(): raise HttpResponseForbidden()
        try:
            sub = Submission.objects.get(competition=competition, members=request.user.profile)
            relation = Relation(submission=sub,profile=request.user.profile)
            if relation.confirmed: raise HttpResponseForbidden()
            else: relation.delete()
        except:
            pass
        submission = Submission.objects.create(competition=competition,modifiedBy=request.user.profile)
        submission.members.add(request.user.profile)
        relation = Relation.objects.get(profile=request.user.profile,submission=submission)
        relation.confirmed = True
        relation.save()
        sendParticipationWelcomeMail(request.user.profile,submission)
        return redirect(competition.getLink())
    except:
        raise Http404()

@login_required
@require_POST
def cancelParticipation(request, compID):
    """
    Withdraw participation
    """
    try:
        competition = Competition.objects.get(id=compID)
        try:
            submission = Submission.objects.get(competition=competition, members=request.user.profile)
            if submission.totalActiveMembers() == 1:
                submission.delete()
            else:
                submission.members.remove(request.user.profile)
            return redirect(competition.getLink(alert="Participation withdrawn."))
        except:
            raise HttpResponseForbidden()
    except:
        raise Http404()

@require_POST
@login_required
def invite(request,subID):
    """
    To invite a member in submission, relation to be confirmed via mail link.
    """
    try:
        emailID = str(request.POST['emailID']).strip().lower()
        if request.user.email == emailID: return JsonResponse({'code': code.NO })
        person = User.objects.get(email=emailID)
        submission = Submission.objects.get(Q(id=subID),~Q(members=person.profile))
        submission.members.add(person.profile)
        sendParticipantInvitationMail(person.profile,request.user.profile,submission)
        return JsonResponse({'code':code.OK})
    except:
        return JsonResponse({'code': code.NO })

@require_GET
@login_required
def invitation(request,subID,userID):
    """
    Renders invitation action page for invitee to which the url was sent via email.
    """
    try:
        if request.user.id != userID: raise Http404()
        user = request.user
        submission = Submission.objects.get(Q(id=subID),Q(submitted=False),~Q(members=user.profile))
        if submission.totalMembers() >= 5: raise Http404()
        try:
            relation = Relation.objects.get(submission=submission,profile=user.profile)
            if relation.confirmed:
                return redirect(submission.competition.getLink(error="You've already participated"))
            else: return render(request, f"{APPNAME}/invitation.html", renderData({
                'submission':submission,
            }, APPNAME))
        except:
            raise Http404()
    except:
        raise Http404()

@require_GET
@login_required
def inviteAction(request,subID,userID,action):
    """
    To accpet/decline participation invitation, by invitee for a submission of a competition.
    """
    try:
        if request.user.id != userID: raise HttpResponseForbidden()
        user = request.user
        submission = Submission.objects.get(id=subID,submitted=False)
        relation = Relation.objects.get(submission=submission,profile=user.profile)
        if relation.confirmed: raise HttpResponseForbidden()
        if action == 'decline':
            relation.delete()
            return render(request, f"{APPNAME}/invitation.html", renderData({
                'submission':submission,
                'declined': True
            }, APPNAME))
        elif action == 'accept':
            relation.confirmed = True
            relation.save()
            sendParticipationWelcomeMail(user.profile,submission)
            return render(request, f"{APPNAME}/invitation.html", renderData({
                'submission':submission,
                'accepted': True
            }, APPNAME))
        else: raise Http404()
    except:
        raise HttpResponseForbidden()



@login_required
@require_POST
def finalSubmit(request, compID, submitID):
    """
    Already existing participation submission
    """
    now = timezone.now()
    try:
        competition = Competition.objects.get(id=compID)
        if competition.endAt < now:
            return redirect(competition.getLink(error="Competition was over before your submission."),permanent=True)
        submission = Submission.objects.get(id=submitID, competition=competition, members=request.user)
        submission.submitOn = now
        submission.submitted = True
        submission.save()
        sendSubmissionConfirmedMail(submission.getMembers(),submission)
        return redirect(competition.getLink(alert="Your submission has been accepted."),permanent=True)
    except:
        return Http404()
