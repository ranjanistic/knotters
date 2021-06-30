from main.methods import renderData
from django.db.models import Q
from django.http.response import Http404, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from people.models import User
from .methods import renderer, sendParticipationWelcomeMail
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from main.strings import code
from people.models import User
from main.decorators import require_JSON_body
from .models import *
from .methods import getCompetitionSectionHTML, getIndexSectionHTML, sendParticipantInvitationMail, sendSubmissionConfirmedMail


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
            raise Exception()
    except:
        raise Http404()


@require_GET
def competition(request, compID):
    try:
        compete = Competition.objects.get(id=compID)
        return renderer(request, 'profile', {"compete": compete})
    except:
        raise Http404()


@require_POST
@require_JSON_body
def data(request, compID):
    try:
        compete = Competition.objects.get(id=compID)
        data = {
            'code': code.OK,
            'timeleft': compete.secondsLeft(),
        }
        if request.user.is_authenticated:
            try:
                subm = Submission.objects.get(
                    competition=compete, members=request.user.profile)
                data['participated'] = True
                data['subID'] = subm.id
            except:
                data['participated'] = False
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'code': code.NO})


@require_GET
def competitionTab(request, compID, section):
    try:
        compete = Competition.objects.get(id=compID)
        data = getCompetitionSectionHTML(compete, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
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
        if not competition.isActive():
            raise Exception()
        try:
            sub = Submission.objects.get(competition=competition, members=request.user.profile)
            relation = Relation.objects.get(submission=sub, profile=request.user.profile)
            if relation.confirmed:
                raise Exception()
            else:
                sub.members.remove(request.user.profile)
        except:
            pass
        submission = Submission.objects.create(
            competition=competition)
        submission.members.add(request.user.profile)
        relation = Relation.objects.get(
            profile=request.user.profile, submission=submission)
        relation.confirmed = True
        relation.save()
        sendParticipationWelcomeMail(request.user.profile, submission)
        return redirect(competition.getLink())
    except Exception as e:
        raise Http404()


@login_required
@require_POST
def removeMember(request, subID, userID):
    """
    Remove member/Withdraw participation
    """
    try:
        if request.user.id == userID:
            member = request.user.profile
        else:
            user = User.objects.get(id=userID)
            member = user.profile

        submission = Submission.objects.get(id=subID, members=member)
        try:
            submission.members.remove(member)
            if submission.totalActiveMembers() == 0:
                submission.delete()
            return redirect(submission.competition.getLink(alert=f"{'Participation withdrawn.' if request.user.profile == member else 'Removed member'}"))
        except Exception as e:
            raise Exception()
    except Exception as e:
        raise Http404()


@require_POST
@require_JSON_body
@login_required
def invite(request, subID):
    """
    To invite a member in submission, relation to be confirmed via mail link.
    """
    try:
        userID = str(request.POST.get('userID', '')).strip().lower()
        if not userID:
            return JsonResponse({'code': code.NO, 'error': 'Invalid ID'})
        if request.user.email == userID or request.user.profile.githubID == userID:
            return JsonResponse({'code': code.NO, 'error': 'You\'re already participating, remember?'})
        try:
            user = User.objects.get(email=userID)
            person = user.profile
        except:
            try:
                person = Profile.objects.get(githubID=userID)
            except:
                person = None
        if not person:
            return JsonResponse({'code': code.NO, 'error': 'User doesn\'t exist.'})
        try:
            Submission.objects.get(members=person)
            return JsonResponse({'code': code.NO, 'error': 'User already participating or invited.'})
        except:
            submission = Submission.objects.get(id=subID)
            submission.members.add(person)
            sendParticipantInvitationMail(
                person, request.user.profile, submission)
            return JsonResponse({'code': code.OK})
    except Exception as e:
        return JsonResponse({'code': code.NO, 'error': str(e)})


@require_GET
@login_required
def invitation(request, subID, userID):
    """
    Renders invitation action page for invitee to which the url was sent via email.
    """
    try:
        if str(request.user.id) != str(userID):
            raise Exception()
        user = request.user
        submission = Submission.objects.get(id=subID, submitted=False)
        if not submission.competition.isActive(): raise Exception()
        if submission.totalMembers() >= 5:
            raise Exception()
        try:
            relation = Relation.objects.get(
                submission=submission, profile=user.profile)
            if relation.confirmed:
                return redirect(submission.competition.getLink(error="You've already participated"))
            else:
                return render(request, "invitation.html", renderData({
                    'submission': submission,
                }, APPNAME))
        except:
            raise Exception()
    except:
        raise Http404()


@require_POST
@login_required
def inviteAction(request, subID, userID, action):
    """
    To accpet/decline participation invitation, by invitee for a submission of a competition.
    """
    try:
        if str(request.user.id) != str(userID):
            raise Exception()
        user = request.user
        submission = Submission.objects.get(id=subID, submitted=False)
        relation = Relation.objects.get(
            submission=submission, profile=user.profile)
        if relation.confirmed:
            raise Exception()
        if action == 'decline':
            relation.delete()
            return render(request, "invitation.html", renderData({
                'submission': submission,
                'declined': True
            }, APPNAME))
        elif action == 'accept':
            relation.confirmed = True
            relation.save()
            sendParticipationWelcomeMail(user.profile, submission)
            return render(request, "invitation.html", renderData({
                'submission': submission,
                'accepted': True
            }, APPNAME))
        else:
            raise Exception()
    except:
        raise Http404()


@login_required
@require_POST
def save(request, compID, subID):
    try:
        competition = Competition.objects.get(id=compID)
        submission = Submission.objects.get(
            id=subID, competition=competition, members=request.user.profile)
        submission.repo = str(request.POST['submissionurl'])
        submission.save()
        return redirect(competition.getLink(alert="Saved"), permanent=True)
    except Exception as e:
        raise Http404()


@login_required
@require_POST
@require_JSON_body
def finalSubmit(request, compID, subID):
    """
    Already existing participation submission
    """
    now = timezone.now()
    try:
        competition = Competition.objects.get(id=compID)
        submission = Submission.objects.get(
            id=subID, competition=competition, members=request.user.profile)
        try:
            relations = Relation.objects.filter(submission=submission,confirmed=False)
            for relation in relations:
                submission.members.remove(relation.profile)
        except:
            pass
        if submission.submitted:
            return JsonResponse({'code': code.OK, 'message': "Already submitted"})
        message = "Submitted successfully"
        if competition.endAt < now:
            if competition.resultDeclared:
                return JsonResponse({'code': code.NO, 'error': "It is too late now."})
            submission.late = True
            message = "Submitted, but late."
        submission.submitOn = now
        submission.submitted = True
        
        submission.save()

        sendSubmissionConfirmedMail(submission.getMembers(), submission)

        return JsonResponse({'code': code.OK, 'message': message})
    except Exception as e:
        raise JsonResponse({'code': code.NO, "error": str(e)})
