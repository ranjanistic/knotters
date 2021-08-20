from uuid import UUID
import os
from django.db.models import Sum
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from main.decorators import require_JSON_body, normal_profile_required, manager_only
from main.methods import errorLog, renderData, respondJson
from main.strings import Action, Code, Message, Template
from people.models import ProfileTopic, Profile
from .models import Competition, ParticipantCertificate, Result, SubmissionParticipant, SubmissionTopicPoint, Submission
from .decorators import judge_only
from .methods import getCompetitionSectionHTML, getIndexSectionHTML, renderer
from .mailers import participantInviteAlert, resultsDeclaredAlert, submissionConfirmedAlert, participantWelcomeAlert, participationWithdrawnAlert
from .apps import APPNAME


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Compete.INDEX)


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
        data = dict(compete=compete)
        if request.user.is_authenticated:
            data = dict(
                **data,
                isJudge=compete.isJudge(request.user.profile),
                isMod=compete.isModerator(request.user.profile),
                isManager=(compete.creator == request.user.profile),
            )
        return renderer(request, Template.Compete.PROFILE, data)
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_JSON_body
def data(request: WSGIRequest, compID: UUID) -> JsonResponse:
    try:
        compete = Competition.objects.get(id=compID)
        data = dict(timeleft=compete.secondsLeft())
        if request.user.is_authenticated:
            try:
                submp = SubmissionParticipant.objects.get(submission__competition=compete, profile=request.user.profile,confirmed=True)
                data = dict(**data,
                    participated=True,
                    subID=submp.submission.getID()
                )
            except:
                data = dict(**data,
                    participated=False,
                )
        return respondJson(Code.OK, data)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@require_GET
def competitionTab(request: WSGIRequest, compID: UUID, section: str) -> HttpResponse:
    try:
        compete = Competition.objects.get(id=compID)
        data = getCompetitionSectionHTML(compete, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def createSubmission(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """
    Take participation
    """
    try:
        now = timezone.now()
        competition = Competition.objects.get(
            id=compID, startAt__lt=now, endAt__gte=now, resultDeclared=False)
        try:
            done = SubmissionParticipant.objects.filter(
                submission__competition=competition, profile=request.user.profile, confirmed=False).delete()
            if not done:
                return redirect(competition.getLink(alert=Message.ALREADY_PARTICIPATING))
        except:
            pass
        if competition.isParticipant(request.user.profile):
            return redirect(competition.getLink(alert=Message.ALREADY_PARTICIPATING))
        submission = Submission.objects.create(competition=competition)
        submission.members.add(request.user.profile)
        SubmissionParticipant.objects.filter(
            submission=submission, profile=request.user.profile).update(confirmed=True)
        request.user.profile.increaseXP(by=5)
        participantWelcomeAlert(request.user.profile, submission)
        return redirect(competition.getLink())
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_JSON_body
def invite(request: WSGIRequest, subID: UUID) -> JsonResponse:
    """
    To invite a member in submission, relation to be confirmed via mail link. (Must not be judge or moderator for the competition)
    """
    try:
        userID = str(request.POST.get('userID', '')).strip().lower()
        if not userID:
            return respondJson(Code.NO, error=Message.INVALID_ID)
        submission = Submission.objects.get(
            id=subID, members=request.user.profile, submitted=False)
        SubmissionParticipant.objects.get(
            submission=submission, profile=request.user.profile, confirmed=True)
        if request.user.email == userID or request.user.profile.githubID == userID:
            return respondJson(Code.NO, error=Message.ALREADY_PARTICIPATING)
        person = Profile.objects.filter(Q(user__email__iexact=userID) | Q(githubID__iexact=userID), Q(
            is_active=True, suspended=False, to_be_zombie=False, is_zombie=False)).first()
        if not person:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        try:
            SubmissionParticipant.objects.get(
                submission__competition=submission.competition, profile=person)
            return respondJson(Code.NO, error=Message.USER_PARTICIPANT_OR_INVITED)
        except:
            if not submission.competition.isActive():
                raise Exception()
            if submission.competition.isJudge(person) or submission.competition.isModerator(person):
                return respondJson(Code.NO, error=Message.USER_PARTICIPANT_OR_INVITED)
            submission.members.add(person)
            participantInviteAlert(person, request.user.profile, submission)
            return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def invitation(request: WSGIRequest, subID: UUID, userID: UUID) -> HttpResponse:
    """
    Renders invitation action page for invitee to which the url was sent via email.
    """
    try:
        if request.user.getID() != userID:
            raise Exception()
        submission = Submission.objects.get(
            id=subID, submitted=False, members=request.user.profile)
        if not submission.competition.isActive() or not submission.canInvite():
            raise Exception()
        try:
            SubmissionParticipant.objects.get(
                submission=submission, profile=request.user.profile, confirmed=False)
            return render(request, Template().invitation, renderData({
                'submission': submission,
            }, APPNAME))
        except:
            return redirect(submission.competition.getLink())
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def inviteAction(request: WSGIRequest, subID: UUID, userID: UUID, action: str) -> HttpResponse:
    """
    To accpet/decline participation invitation, by invitee for a submission of a competition.
    """
    try:
        if request.user.getID() != userID:
            raise Exception()
        submission = Submission.objects.get(
            id=subID, submitted=False, members=request.user.profile)
        if not submission.competition.isActive():
            raise Exception()
        if action == Action.DECLINE:
            SubmissionParticipant.objects.filter(
                submission=submission, profile=request.user.profile, confirmed=False).delete()
            return render(request, Template().invitation, renderData(dict(
                submission=submission,
                declined=True
            ), APPNAME))
        elif action == Action.ACCEPT:
            SubmissionParticipant.objects.filter(
                submission=submission, profile=request.user.profile, confirmed=False).update(confirmed=True)
            request.user.profile.increaseXP(by=5)
            participantWelcomeAlert(request.user.profile, submission)
            return render(request, Template().invitation, renderData(dict(
                submission=submission,
                accepted=True
            ), APPNAME))
        else:
            raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def removeMember(request: WSGIRequest, subID: UUID, userID: UUID) -> HttpResponse:
    """
    Remove member/Withdraw participation
    """
    try:
        member = request.user.profile if request.user.getID(
        ) == userID else Profile.objects.get(user__id=userID)
        submission = Submission.objects.get(
            id=subID, members=member, submitted=False, competition__resultDeclared=False)
        SubmissionParticipant.objects.get(
            submission=submission, profile=request.user.profile, confirmed=True)
        if not submission.competition.isActive():
            raise Exception()
        try:
            submission.members.remove(member)
            if submission.totalActiveMembers() == 0:
                submission.delete()
            member.decreaseXP(by=5)
            participationWithdrawnAlert(member, submission)
            return redirect(submission.competition.getLink(alert=f"{Message.PARTICIPATION_WITHDRAWN if request.user.profile == member else Message.MEMBER_REMOVED}"))
        except Exception as e:
            errorLog(e)
            raise Exception(e)
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def save(request: WSGIRequest, compID: UUID, subID: UUID) -> HttpResponse:
    try:
        now = timezone.now()
        subm = Submission.objects.get(id=subID, competition__id=compID, competition__startAt__lt=now,
                                      competition__endAt__gte=now, competition__resultDeclared=False, members=request.user.profile
                                      )
        subm.repo = str(request.POST.get('submissionurl', '')).strip()
        subm.modifiedOn = now
        subm.save()
        return redirect(subm.competition.getLink(alert=Message.SAVED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_JSON_body
def finalSubmit(request: WSGIRequest, compID: UUID, subID: UUID) -> JsonResponse:
    """
    Already existing participation final submission
    """
    try:
        now = timezone.now()
        submission = Submission.objects.get(
            id=subID, competition__id=compID, competition__resultDeclared=False, members=request.user.profile, submitted=False)
        message = Message.SUBMITTED_SUCCESS
        if submission.competition.endAt < now:
            submission.late = True
            message = Message.SUBMITTED_LATE
        if submission.isInvitee(request.user.profile):
            raise Exception()
        SubmissionParticipant.objects.filter(
            submission=submission, confirmed=False).delete()
        submission.submitOn = now
        submission.submitted = True
        submission.save()
        for member in submission.getMembers():
            member.increaseXP(by=2)
        submissionConfirmedAlert(submission)
        return respondJson(Code.OK, message=message)
    except Exception as e:
        errorLog(e)
        raise respondJson(Code.NO, error=Message.ERROR_OCCURRED)

@normal_profile_required
@judge_only
@require_JSON_body
def submitPoints(request: WSGIRequest, compID: UUID) -> JsonResponse:
    """
    For judge to submit their markings of all submissions of a competition.
    """
    try:
        subs = request.POST.get('submissions', None)
        if not subs:
            return respondJson(Code.NO, error=Message.SUBMISSION_MARKING_INVALID)

        submissions = Submission.objects.filter(competition__id=compID, competition__judges=request.user.profile,
                                                competition__resultDeclared=False, competition__endAt__lt=timezone.now(), valid=True).order_by('submitOn')

        competition = submissions.first().competition

        if competition.allSubmissionsMarkedByJudge(judge=request.user.profile):
            raise Exception()

        topics = competition.getTopics()

        modifiedTops = {}

        for top in topics:
            modifiedTops[str(top.getID())] = []

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
            subspointslist = modifiedTops[str(topic.getID())]
            for sub in subspointslist:
                point = None
                submission = None
                for subm in submissions:
                    if sub.keys().__contains__(str(subm.getID())):
                        submission = subm
                        point = int(sub[str(subm.getID())])
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

        subtopicpoints = SubmissionTopicPoint.objects.bulk_create(topicpointsList)
        request.user.profile.increaseXP(by=len(submissions))
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_POST
def declareResults(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """
    For manager to declare results after markings of all submissions by all judges have been completed.
    """
    try:
        comp = Competition.objects.get(
            id=compID, endAt__lt=timezone.now(), resultDeclared=False,creator=request.user.profile)

        if not (comp.moderated() and comp.allSubmissionsMarked()):
            return redirect(comp.getJudgementLink(error=Message.INVALID_REQUEST))

        declared = comp.declareResults()
        if not declared:
            return redirect(comp.getJudgementLink(error=Message.ERROR_OCCURRED))

        resultsDeclaredAlert(competition=declared)
        return redirect(comp.getJudgementLink(alert=Message.RESULT_DECLARED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
def claimXP(request: WSGIRequest, compID: UUID, subID: UUID) -> HttpResponse:
    try:
        result = Result.objects.get(submission__competition__id=compID,
                                    submission__id=subID, submission__members=request.user.profile)
        if request.user.profile in result.xpclaimers.all():
            raise Exception()
        profile = Profile.objects.get(user=request.user)
        profile.increaseXP(by=result.points)
        result.xpclaimers.add(profile)
        topicpoints = SubmissionTopicPoint.objects.filter(
            submission=result.submission).values('topic').annotate(points=Sum('points'))
        proftops = ProfileTopic.objects.filter(profile=request.user.profile)
        for topicpoint in topicpoints:
            for proftop in proftops:
                if proftop.topic.id == topicpoint['topic']:
                    try:
                        finaltop = ProfileTopic.objects.get(
                            profile=request.user.profile, topic=proftop.topic)
                        finaltop.increasePoints(by=topicpoint['points'])
                    except Exception as e:
                        ProfileTopic.objects.create(
                            profile=request.user.profile, topic=proftop.topic, trashed=True, points=topicpoint['points'])
                        errorLog(e)
                        pass

        return redirect(result.submission.competition.getLink(alert=Message.XP_ADDED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@manager_only
@require_POST
def generateCertificates(request:WSGIRequest, compID:UUID) -> HttpResponse:
    try:
        competition = Competition.objects.get(id=compID,creator=request.user.profile)
        if not (competition.resultDeclared and competition.allResultsDeclared()):
            raise Exception('Results not declared')
        if competition.certificatesGenerated():
            raise Exception("Certs already generated")
        participantCerts = []
        for result in competition.getResults():
            for member in result.submission.getMembers():
                raise Exception('gen_certificate: Not yet supported')
                # TODO: Generate certificates in media
                # participantCerts.append(
                #     ParticipantCertificate(
                #         result=result,
                #         profile=member,
                #         certificate=''
                #     )
                # )
        certs = ParticipantCertificate.objects.bulk_create(participantCerts,batch_size=100)
        return len(certs) == competition.totalParticipants()
    except Exception as e:
        errorLog(e)
        raise Http404()

@require_GET
def certificate(request: WSGIRequest, resID: UUID, userID: UUID) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.getID() == userID:
            self = True
            member = request.user.profile
        else:
            self = False
            member = Profile.objects.get(user__id=userID,suspended=False,is_active=True,is_zombie=False,to_be_zombie=False)
        result = Result.objects.get(id=resID, submission__members=member)

        partcert = ParticipantCertificate.objects.filter(
            result__id=resID, profile=member).first()

        certpath = False if not partcert else partcert.getCertificate()
        return renderer(request, Template.Compete.CERTIFICATE, dict(result=result, member=member, certpath=certpath, self=self))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
def downloadCertificate(request: WSGIRequest, resID: UUID, userID: UUID) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.getID() == userID:
            member = request.user.profile
        else:
            member = Profile.objects.get(user__id=userID)
        partcert = ParticipantCertificate.objects.get(
            result__id=resID, profile=member)

        file_path = os.path.join(settings.MEDIA_ROOT, str(partcert.certificate))
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type="image/jpg")
                response['Content-Disposition'] = 'inline; filename=' + \
                    os.path.basename(file_path)
                return response
        raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()
