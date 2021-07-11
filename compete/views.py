from people.decorators import profile_active_required
from django.core.handlers.wsgi import WSGIRequest
from uuid import UUID
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from main.decorators import require_JSON_body
from main.methods import renderData
from main.strings import Action, code
from people.models import User, Profile
from moderation.decorators import moderator_only
from .models import Competition, SubmissionParticipant, SubmissionTopicPoint, Submission
from .decorators import judge_only
from .apps import APPNAME
from .methods import getCompetitionSectionHTML, getIndexSectionHTML, renderer
from .mailers import sendParticipantInvitationMail, sendSubmissionConfirmedMail, sendParticipationWelcomeMail


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, 'index')


@require_GET
def indexTab(request: WSGIRequest, tab: str) -> HttpResponse:
    try:
        data = getIndexSectionHTML(section=tab, request=request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
    except:
        raise Http404()


@require_GET
def competition(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        compete = Competition.objects.get(id=compID)
        data = {"compete": compete}
        if request.user.is_authenticated:
            data["isJudge"] = compete.isJudge(request.user.profile)
            data["isMod"] = compete.isModerator(request.user.profile)
        return renderer(request, 'profile', data)
    except Exception as e:
        print(e)
        raise Http404()


@require_JSON_body
def data(request: WSGIRequest, compID: UUID) -> JsonResponse:
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
def competitionTab(request: WSGIRequest, compID: UUID, section: str) -> HttpResponse:
    try:
        compete = Competition.objects.get(id=compID)
        data = getCompetitionSectionHTML(compete, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
    except:
        raise Http404()


@require_POST
@login_required
@profile_active_required
def createSubmission(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """
    Take participation
    """
    try:
        competition = Competition.objects.get(id=compID)
        if not competition.isActive():
            raise Exception()
        try:
            sub = Submission.objects.get(
                competition=competition, members=request.user.profile)
            relation = SubmissionParticipant.objects.get(
                submission=sub, profile=request.user.profile)
            if not relation.confirmed:
                sub.members.remove(request.user.profile)
            else:
                return redirect(competition.getLink(alert="You're already participating."))
        except:
            pass
        submission = Submission.objects.create(
            competition=competition)
        submission.members.add(request.user.profile)
        SubmissionParticipant.objects.filter(
            submission=submission, profile=request.user.profile).update(confirmed=True)
        sendParticipationWelcomeMail(request.user.profile, submission)
        return redirect(competition.getLink())
    except Exception as e:
        raise Http404()


@require_POST
@login_required
@profile_active_required
def removeMember(request: WSGIRequest, subID: UUID, userID: UUID) -> HttpResponse:
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
        if not submission.competition.isActive():
            raise Exception()
        try:
            submission.members.remove(member)
            if submission.totalActiveMembers() == 0:
                submission.delete()
            return redirect(submission.competition.getLink(alert=f"{'Participation withdrawn.' if request.user.profile == member else 'Removed member'}"))
        except Exception as e:
            raise Exception()
    except Exception as e:
        raise Http404()


@require_JSON_body
@login_required
@profile_active_required
def invite(request: WSGIRequest, subID: UUID) -> JsonResponse:
    """
    To invite a member in submission, relation to be confirmed via mail link. (Must not be judge or moderator for the competition)
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
            if not submission.competition.isActive():
                raise Exception()
            if submission.competition.isJudge(person) or submission.competition.isModerator(person):
                return JsonResponse({'code': code.NO, 'error': 'User already participating or invited.'})
            submission.members.add(person)
            sendParticipantInvitationMail(
                person, request.user.profile, submission)
            return JsonResponse({'code': code.OK})
    except Exception as e:
        return JsonResponse({'code': code.NO, 'error': str(e)})


@require_GET
@login_required
@profile_active_required
def invitation(request: WSGIRequest, subID: UUID, userID: UUID) -> HttpResponse:
    """
    Renders invitation action page for invitee to which the url was sent via email.
    """
    try:
        if str(request.user.id) != str(userID):
            raise Exception()
        user = request.user
        submission = Submission.objects.get(id=subID, submitted=False)
        if not submission.competition.isActive():
            raise Exception()
        if not submission.canInvite():
            raise Exception()
        try:
            relation = SubmissionParticipant.objects.get(
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
@profile_active_required
def inviteAction(request: WSGIRequest, subID: UUID, userID: UUID, action: str) -> HttpResponse:
    """
    To accpet/decline participation invitation, by invitee for a submission of a competition.
    """
    try:
        if str(request.user.id) != str(userID):
            raise Exception()
        
        submission = Submission.objects.get(id=subID, submitted=False)
        if not submission.competition.isActive():
            raise Exception()
        if action == Action.DECLINE:
            SubmissionParticipant.objects.filter(submission=submission, profile=request.user.profile, confirmed=False).delete()
            return render(request, "invitation.html", renderData({
                'submission': submission,
                'declined': True
            }, APPNAME))
        elif action == Action.ACCEPT:
            SubmissionParticipant.objects.filter(submission=submission, profile=request.user.profile, confirmed=False).update(confirmed=True)
            sendParticipationWelcomeMail(request.user.profile, submission)
            return render(request, "invitation.html", renderData({
                'submission': submission,
                'accepted': True
            }, APPNAME))
        else:
            raise Exception()
    except:
        raise Http404()


@require_POST
@login_required
@profile_active_required
def save(request: WSGIRequest, compID: UUID, subID: UUID) -> HttpResponse:
    try:
        now = timezone.now()
        competition = Competition.objects.get(id=compID)
        if not competition.isActive():
            raise Exception()
        Submission.objects.filter(id=subID, competition=competition, members=request.user.profile).update(
            repo=str(request.POST.get('submissionurl', '')), modifiedOn=now)
        return redirect(competition.getLink(alert="Saved"), permanent=True)
    except Exception as e:
        raise Http404()


@require_JSON_body
@login_required
@profile_active_required
def finalSubmit(request: WSGIRequest, compID: UUID, subID: UUID) -> JsonResponse:
    """
    Already existing participation final submission
    """
    now = timezone.now()
    try:
        competition = Competition.objects.get(id=compID)
        submission = Submission.objects.get(
            id=subID, competition=competition, members=request.user.profile)
        if submission.submitted:
            return JsonResponse({'code': code.OK, 'message': "Already submitted"})
        message = "Submitted successfully"
        if competition.endAt < now:
            if competition.resultDeclared:
                return JsonResponse({'code': code.NO, 'error': "It is too late now."})
            submission.late = True
            message = "Submitted, but late."
        try:
            SubmissionParticipant.objects.filter(submission=submission, confirmed=False).delete()
        except:
            pass
        submission.submitOn = now
        submission.submitted = True
        submission.save()
        sendSubmissionConfirmedMail(submission.getMembers(), submission)
        return JsonResponse({'code': code.OK, 'message': message})
    except Exception as e:
        print(e)
        raise JsonResponse({'code': code.NO, "error": "An error occurred"})


@require_JSON_body
@judge_only
def submitPoints(request: WSGIRequest, compID: UUID) -> JsonResponse:
    try:
        subs = request.POST.get('submissions', None)
        if not subs:
            return JsonResponse({'code': code.NO, 'error': 'Invalid submission markings, try again.'})

        comp = Competition.objects.get(
            id=compID, judges=request.user.profile, resultDeclared=False, endAt__lt=timezone.now())
        submissions = comp.getValidSubmissions()
        topics = comp.getTopics()

        modifiedTops = {}

        for top in topics:
            modifiedTops[str(top.id)] = []

        for sub in subs:
            subID = str(sub['subID']).strip()
            for top in sub['topics']:
                topID = str(top['topicID']).strip()
                points = int(top['points'])
                modifiedTops[topID].append({
                    subID: points
                })

        topicpointsList = []
        for topic in topics:
            subspointslist = modifiedTops[str(topic.id)]
            for sub in subspointslist:
                point = None
                submission = None
                for subm in submissions:
                    if sub.keys().__contains__(str(subm.id)):
                        submission = subm
                        point = int(sub[str(subm.id)])
                        break
                if point == None or submission == None:
                    raise Exception()
                else:
                    topicpointsList.append(SubmissionTopicPoint(
                        submission=submission,
                        topic=topic,
                        judge=request.user.profile,
                        points=point
                    ))

        SubmissionTopicPoint.objects.bulk_create(topicpointsList)
        return JsonResponse({'code': code.OK})
    except Exception as e:
        print(e)
        return JsonResponse({'code': code.NO, 'error': 'An error occurred'})


@require_POST
@moderator_only
def declareResults(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        comp = Competition.objects.get(
            id=compID, endAt__lt=timezone.now(), resultDeclared=False)

        if not comp.isModerator(request.user.profile):
            raise Exception()
        if not (comp.moderated() and comp.allSubmissionsMarked()):
            return redirect(comp.getJudgementLink(error="Invalid request"))

        declared = comp.declareResults()
        if not declared:
            return redirect(comp.getJudgementLink(error="An error occurred."))
        return redirect(comp.getJudgementLink(alert="Results declared!"))
    except Exception as e:
        print(e)
        raise Http404()
