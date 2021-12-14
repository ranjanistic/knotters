from uuid import UUID
from ratelimit.decorators import ratelimit
import os
from django.db.models import Sum
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import Http404, HttpResponse, HttpResponseForbidden, HttpResponseServerError, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from allauth.account.models import EmailAddress
from main.decorators import require_JSON_body, normal_profile_required, manager_only
from main.methods import addMethodToAsyncQueue, errorLog, renderData, respondJson, respondRedirect
from main.strings import Action, Code, Message, Template, URL
from people.models import ProfileTopic, Profile, Topic
from .models import Competition, ParticipantCertificate, AppreciationCertificate, Result, SubmissionParticipant, SubmissionTopicPoint, Submission
from .decorators import judge_only
from .methods import DeclareResults, getCompetitionSectionHTML, getIndexSectionHTML, renderer, AllotCompetitionCertificates
from .mailers import participantInviteAlert, submissionConfirmedAlert, participantWelcomeAlert, participationWithdrawnAlert, submissionsJudgedAlert
from .apps import APPNAME


@require_GET
# @cache_page(settings.CACHE_LONG)
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
        data = dict(timeleft=compete.secondsLeft(),
                    startTimeLeft=compete.startSecondsLeft())
        if request.user.is_authenticated:
            try:
                submp = SubmissionParticipant.objects.get(
                    submission__competition=compete, profile=request.user.profile, confirmed=True)
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
@ratelimit(key='user', rate='10/m', block=True, method=('POST'))
def createSubmission(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """
    Take participation
    """
    try:
        now = timezone.now()
        competition = Competition.objects.get(
            id=compID, startAt__lt=now, endAt__gte=now, resultDeclared=False)
        try:
            # filter.delete doesn't work !?
            subpart = SubmissionParticipant.objects.get(
                submission__competition=competition, profile=request.user.profile, confirmed=False)
            subpart.delete()
        except Exception as e:
            pass
        if competition.isNotAllowedToParticipate(request.user.profile):
            return HttpResponseForbidden()
        if competition.isParticipant(request.user.profile):
            return redirect(competition.getLink(alert=Message.ALREADY_PARTICIPATING))
        submission = Submission.objects.create(competition=competition)
        submission.members.add(request.user.profile)
        SubmissionParticipant.objects.filter(
            submission=submission, profile=request.user.profile).update(confirmed=True)
        request.user.profile.increaseXP(by=5)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{participantWelcomeAlert.__name__}", request.user.profile, submission)
        return redirect(competition.getLink(alert=Message.PARTICIPATION_CONFIRMED))
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_JSON_body
@ratelimit(key='user', rate='5/m', block=True, method=('POST'))
def invite(request: WSGIRequest, subID: UUID) -> JsonResponse:
    """
    To invite a member in submission, relation to be confirmed via mail link. (Must not be judge or moderator for the competition)
    """
    try:
        userID = str(request.POST.get('userID', '')).strip().lower()
        if not userID or userID == 'None':
            return respondJson(Code.NO, error=Message.INVALID_ID)
        submission = Submission.objects.get(
            id=subID, members=request.user.profile, submitted=False)
        SubmissionParticipant.objects.get(
            submission=submission, profile=request.user.profile, confirmed=True)
        if request.user.email.lower() == userID or str(request.user.profile.ghID).lower() == userID:
            return respondJson(Code.NO, error=Message.ALREADY_PARTICIPATING)
        person = Profile.objects.filter(Q(user__email__iexact=userID) | Q(githubID__iexact=userID), Q(
            is_active=True, suspended=False, to_be_zombie=False, user__emailaddress__verified=True)).first()
        if not person:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        if person.isBlocked(request.user):
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST)
        if not submission.competition.isAllowedToParticipate(person):
            return respondJson(Code.NO, error=Message.USER_PARTICIPANT_OR_INVITED)

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
            addMethodToAsyncQueue(
                f'{APPNAME}.mailers.{participantInviteAlert.__name__}', person, request.user.profile, submission)
            return respondJson(Code.OK)
    except Exception as e:
        print(e)
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
        if not submission.competition.isActive():
            raise Exception()
        if not submission.competition.isAllowedToParticipate(request.user.profile):
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
        if not submission.competition.isAllowedToParticipate(request.user.profile):
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
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{participantWelcomeAlert.__name__}", request.user.profile, submission)
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
            conf = SubmissionParticipant.objects.filter(profile=member, submission=submission, confirmed=True).first()
            submission.members.remove(member)
            if submission.totalActiveMembers() == 0:
                submission.delete()
            if conf:
                member.decreaseXP(by=5)
                addMethodToAsyncQueue(
                    f"{APPNAME}.mailers.{participationWithdrawnAlert.__name__}", member, submission)
            return redirect(submission.competition.getLink(alert=f"{Message.PARTICIPATION_WITHDRAWN if request.user.profile == member else Message.MEMBER_REMOVED}"))
        except Exception as e:
            errorLog(e)
            raise Exception(e)
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='5/s', block=True, method=('POST'))
def save(request: WSGIRequest, compID: UUID, subID: UUID) -> HttpResponse:
    try:
        now = timezone.now()
        subm = Submission.objects.get(id=subID, competition__id=compID, competition__startAt__lt=now,
                                      competition__endAt__gte=now, competition__resultDeclared=False, members=request.user.profile
                                      )
        if not subm.competition.isAllowedToParticipate(request.user.profile):
            raise Exception()
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
        if submission.isInvitee(request.user.profile):
            raise Exception()
        if not submission.competition.isAllowedToParticipate(request.user.profile):
            raise Exception()
        if submission.competition.moderated():
            return respondJson(Code.OK, error=Message.SUBMISSION_TOO_LATE)
        if submission.competition.endAt < now:
            submission.late = True
            message = Message.SUBMITTED_LATE
        SubmissionParticipant.objects.filter(
            submission=submission, confirmed=False).delete()
        submission.submitOn = now
        submission.submitted = True
        submission.save()
        for member in submission.getMembers():
            member.increaseXP(by=2)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{submissionConfirmedAlert.__name__}", submission)
        return respondJson(Code.OK, message=message)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@judge_only
@require_JSON_body
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
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
        if competition.isAllowedToParticipate(request.user.profile):
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

        subtopicpoints = SubmissionTopicPoint.objects.bulk_create(
            topicpointsList)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{submissionsJudgedAlert.__name__}", competition, request.user.profile)
            
        judgeXP = len(submissions)//(len(topics)+1)
        for topic in topics:
            profiletopic, created = ProfileTopic.objects.get_or_create(
                profile=request.user.profile,
                topic=topic,
                defaults=dict(
                    profile=request.user.profile,
                    topic=topic,
                    trashed=True,
                    points=judgeXP
                )
            )
            if not created:
                profiletopic.increasePoints(by=judgeXP)
        request.user.profile.increaseXP(by=judgeXP)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def declareResults(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """
    For manager to declare results after markings of all submissions by all judges have been completed.
    """
    try:
        comp = Competition.objects.get(
            id=compID, endAt__lt=timezone.now(), resultDeclared=False, creator=request.user.profile)

        if comp.isAllowedToParticipate(request.user.profile):
            raise Exception()

        if not (comp.moderated() and comp.allSubmissionsMarked()):
            return redirect(comp.getManagementLink(error=Message.INVALID_REQUEST))
        task = cache.get(f"results_declaration_task_{compID}")
        if task == Message.RESULT_DECLARING:
            return redirect(comp.getManagementLink(error=Message.RESULT_DECLARING))
        cache.set(f"results_declaration_task_{comp.get_id}",
                  Message.RESULT_DECLARING, settings.CACHE_ETERNAL)
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{DeclareResults.__name__}", comp)
        return redirect(comp.getManagementLink(alert=Message.RESULT_DECLARING))
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
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
        topicpointsIDs = []
        for topicpoint in topicpoints:
            topicpointsIDs.append(topicpoint['topic'])
        topics = Topic.objects.filter(id__in=topicpointsIDs)
        for topic in topics:
            profiletopic, _ = ProfileTopic.objects.get_or_create(
                profile=request.user.profile,
                topic=topic,
                defaults=dict(
                    profile=request.user.profile,
                    topic=topic,
                    trashed=True
                )
            )
            for topicpoint in topicpoints:
                if topicpoint['topic'] == topic.id:
                    profiletopic.increasePoints(by=topicpoint['points'])
                    break

        return redirect(result.submission.competition.getLink(alert=Message.XP_ADDED))
    except Exception as e:
        errorLog(e)
        raise Http404()


# @normal_profile_required
@require_JSON_body
def getTopicScores(request: WSGIRequest, resID: UUID) -> JsonResponse:
    try:
        result = cache.get(f"competition_result_{resID}")
        if not result:
            result = Result.objects.get(id=resID)
            cache.set(f"competition_result_{resID}",
                      result, settings.CACHE_MAX)
        topics = []
        for top in result.topic_points:
            topics.append(dict(
                id=top["topic__id"],
                name=top["topic__name"],
                score=top["score"]
            ))
        return respondJson(Code.OK, dict(topics=topics))
    except Exception as e:
        print(e)
        return respondJson(Code.NO)


@require_GET
# @cache_page(settings.CACHE_LONG)
def certificateIndex(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Compete.CERT_INDEX)


@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def certificateVerify(request: WSGIRequest) -> HttpResponse:
    certID = request.POST.get('certID', request.GET.get('id', None))
    try:
        if not certID:
            return respondRedirect(APPNAME, URL.Compete.CERT_INDEX, error=Message.INVALID_REQUEST)
        partcert = ParticipantCertificate.objects.filter(
            id=UUID(str(certID).strip())).first()
        if partcert and partcert.certificate:
            return respondRedirect(APPNAME, URL.compete.certficate(partcert.result.getID(), partcert.profile.getUserID()))

        appcert = AppreciationCertificate.objects.filter(
            id=UUID(str(certID).strip())).first()
        if appcert and appcert.certificate:
            return respondRedirect(APPNAME, URL.compete.apprCertificate(appcert.competition.get_id, appcert.appreciatee.getUserID()))

        return respondRedirect(APPNAME, f"{URL.Compete.CERT_INDEX}?certID={certID}", error=Message.CERT_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, f"{URL.Compete.CERT_INDEX}?certID={certID}", error=Message.CERT_NOT_FOUND)


@require_GET
# @cache_page(settings.CACHE_MINI)
def certificate(request: WSGIRequest, resID: UUID, userID: UUID) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.getID() == userID:
            self = True
            member = request.user.profile
        else:
            self = False
            member = Profile.objects.get(
                user__id=userID, suspended=False, to_be_zombie=False)

        if request.user.is_authenticated and member.isBlocked(request.user):
            raise Exception()

        result = Result.objects.get(id=resID, submission__members=member)

        partcert = ParticipantCertificate.objects.filter(
            result__id=resID, profile=member).first()

        certpath = False if not partcert else partcert.getCertImage if partcert.certificate else False
        certID = False if not partcert else partcert.get_id
        return renderer(request, Template.Compete.CERT_CERTIFICATE, dict(result=result, member=member, certpath=certpath, self=self, certID=certID))
    except Exception as e:
        errorLog(e)
        raise Http404()


@require_GET
# @cache_page(settings.CACHE_MINI)
def appCertificate(request: WSGIRequest, compID: UUID, userID: UUID) -> HttpResponse:
    try:
        if request.user.is_authenticated and request.user.getID() == userID:
            self = True
            person = request.user.profile
        else:
            self = False
            person = Profile.objects.get(
                user__id=userID, suspended=False, to_be_zombie=False)

        if request.user.is_authenticated and person.isBlocked(request.user):
            raise Exception()

        appcert = AppreciationCertificate.objects.filter(
            competition__id=compID, appreciatee=person).first()

        certpath = False if not appcert else appcert.getCertImage if appcert.certificate else False
        certID = False if not appcert else appcert.get_id
        if appcert:
            compete = appcert.competition
        else:
            compete = Competition.objects.get(id=compID)
        return renderer(request, Template.Compete.CERT_APPCERTIFICATE, dict(compete=compete, appcert=appcert, person=person, certpath=certpath, self=self, certID=certID))
    except Exception as e:
        raise Http404()


@manager_only
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def generateCertificates(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        competition = Competition.objects.get(
            id=compID, creator=request.user.profile, resultDeclared=True)
        if not (competition.resultDeclared and competition.allResultsDeclared()):
            return redirect(competition.getManagementLink(alert=Message.RESULT_NOT_DECLARED))
        if competition.certificatesGenerated():
            return redirect(competition.getManagementLink(alert=Message.CERTS_GENERATED))
        if cache.get(f"certificates_allotment_task_{competition.get_id}") == Message.CERTS_GENERATING:
            return redirect(competition.getManagementLink(alert=Message.CERTS_GENERATING))
        doneresultIDs = ParticipantCertificate.objects.filter(
            result__competition=competition).values_list("result__id", flat=True)
        if(len(doneresultIDs) > 0):
            remainingresults = Result.objects.filter(
                ~Q(id__in=doneresultIDs), competition=competition)
        else:
            remainingresults = Result.objects.filter(competition=competition)
        cache.set(f"certificates_allotment_task_{competition.get_id}",
                  Message.CERTS_GENERATING, settings.CACHE_ETERNAL)
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{AllotCompetitionCertificates.__name__}", remainingresults, competition)
        return redirect(competition.getManagementLink(alert=Message.CERTS_GENERATING))
    except Exception as e:
        errorLog(e)
        return HttpResponseServerError(e)


@normal_profile_required
@require_GET
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def downloadCertificate(request: WSGIRequest, resID: UUID, userID: UUID) -> HttpResponse:
    try:
        if request.user.getID() == userID:
            member = request.user.profile
        else:
            raise Exception()
        partcert = ParticipantCertificate.objects.get(
            result__id=resID, profile=member)

        file_path = os.path.join(
            settings.MEDIA_ROOT, str(partcert.certificate))
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(
                    fh.read(), content_type="application/pdf")
                response['Content-Disposition'] = 'inline; filename=' + \
                    os.path.basename(file_path)
                return response
        raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()


@normal_profile_required
@require_GET
@ratelimit(key='user', rate='1/s', block=True, method=('POST'))
def appDownloadCertificate(request: WSGIRequest, compID: UUID, userID: UUID) -> HttpResponse:
    try:
        if request.user.getID() == userID:
            person = request.user.profile
        else:
            raise Exception()
        appcert = AppreciationCertificate.objects.get(
            competition__id=compID, appreciatee=person)

        file_path = os.path.join(settings.MEDIA_ROOT, str(appcert.certificate))
        if os.path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(
                    fh.read(), content_type="application/pdf")
                response['Content-Disposition'] = 'inline; filename=' + \
                    os.path.basename(file_path)
                return response
        raise Exception()
    except Exception as e:
        errorLog(e)
        raise Http404()
