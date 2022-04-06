from os import path as os_path
from uuid import UUID

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q, Sum
from django.http.response import (Http404, HttpResponse,
                                  HttpResponseServerError, JsonResponse)
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from main.decorators import (decode_JSON, manager_only, mentor_only,
                             normal_profile_required, require_JSON)
from main.exceptions import InactiveCompetitionError
from main.methods import (addMethodToAsyncQueue, errorLog, respondJson,
                          respondRedirect)
from main.strings import URL, Action, Code, Message, Template
from people.models import Profile, ProfileTopic, Topic
from projects.models import FreeProject
from ratelimit.decorators import ratelimit

from .apps import APPNAME
from .mailers import (participantInviteAlert, participantWelcomeAlert,
                      participationWithdrawnAlert, submissionConfirmedAlert,
                      submissionsJudgedAlert)
from .methods import (AllotCompetitionCertificates, DeclareResults,
                      competitionProfileData, getCompetitionSectionHTML,
                      getIndexSectionHTML, renderer, rendererstrResponse)
from .models import (AppreciationCertificate, Competition,
                     ParticipantCertificate, Result, Submission,
                     SubmissionParticipant, SubmissionTopicPoint)
from .receivers import *


@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    """The home page of competitions.

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: text/html response with index page
    """
    return renderer(request, Template.Compete.INDEX)


@require_GET
def indexTab(request: WSGIRequest, tab: str) -> HttpResponse:
    """To handle competitions homepage tabs request.

    Args:
        request (WSGIRequest): The request object.
        tab (str): The type of tab content requested (active|upcoming|history)

    Raises:
        Exception: If tab is not one of active|upcoming|history
        Http404: If tab section html is not found

    Returns:
        HttpResponse: text/html response with tab section html content
    """
    try:
        data = getIndexSectionHTML(section=tab, request=request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception(tab)
    except Exception as e:
        raise Http404(e)


@require_GET
def competition(request: WSGIRequest, compID: str) -> HttpResponse:
    """To handle competition profile request.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID, str): The competition UUID or nickname

    Raises:
        Http404: If competition is not found, or is not available to be viewed

    Returns:
        HttpResponseRedirect: If competition ID is UUID, redirect to nickname based URL
        HttpResponse: text/html response with competition profile page
    """
    try:
        try:
            compID = UUID(compID)
            isuuid = True
        except:
            isuuid = False

        if isuuid:
            data = competitionProfileData(request, compID=compID)
        else:
            data = competitionProfileData(request, nickname=compID)
        if not data:
            raise ObjectDoesNotExist(compID)
        compete = data['compete']
        if isuuid:
            return redirect(compete.getLink())
        if compete.is_draft:
            if data["isManager"]:
                return redirect(compete.getManagementLink())
            raise ObjectDoesNotExist('isdraft: ', compete)
        return renderer(request, Template.Compete.PROFILE, data)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_JSON
def data(request: WSGIRequest, compID: UUID) -> JsonResponse:
    """To provide additional competition data.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID

    Returns:
        JsonResponse: response main.strings.Code.OK with additional competition data (timeleft, participated, etc.) if available else main.strings.Code.NO
    """
    try:
        compete = Competition.objects.get(id=compID, is_draft=False)
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
            except ObjectDoesNotExist:
                data = dict(**data,
                            participated=False,
                            )
        return respondJson(Code.OK, data)
    except ObjectDoesNotExist as o:
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@require_GET
def competitionTab(request: WSGIRequest, compID: UUID, section: str) -> HttpResponse:
    """To handle competition profile tabs section request.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID
        section (str): The type of tab content requested (overview|task|guidelines|submission|results)

    Raises:
        Http404: If competition or section is not found, or is not available to be viewed

    Returns:
        HttpResponse: text/html response with tab section html content
    """
    try:
        compete = Competition.objects.get(id=compID, is_draft=False)
        data = getCompetitionSectionHTML(compete, section, request)
        if data:
            return HttpResponse(data)
        else:
            raise Exception()
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='10/m', block=True, method=(Code.POST))
def createSubmission(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """To create a new submission.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID

    Raises:
        Http404: If competition is not found

    Returns:
        HttpResponseRedirect: redirect to competition profile page with relevant message, if submission is already created,
            or not allowed to create submission, or submission is created successfully
    """
    try:
        now = timezone.now()
        competition = Competition.objects.get(
            id=compID, startAt__lt=now, endAt__gte=now, resultDeclared=False, is_draft=False)
        try:
            # NOTE filter.delete doesn't work !?
            subpart = SubmissionParticipant.objects.get(
                submission__competition=competition, profile=request.user.profile, confirmed=False)
            subpart.delete()
        except ObjectDoesNotExist:
            pass
        if competition.isNotAllowedToParticipate(request.user.profile):
            return redirect(competition.getLink(alert=Message.PARTICIPATION_PROHIBITED))
        if competition.isParticipant(request.user.profile):
            return redirect(competition.getLink(alert=Message.ALREADY_PARTICIPATING))
        submission = Submission.objects.create(competition=competition)
        submission.members.add(request.user.profile)
        SubmissionParticipant.objects.filter(submission=submission, profile=request.user.profile).update(
            confirmed=True, confirmed_on=submission.createdOn)
        request.user.profile.increaseXP(by=5)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{participantWelcomeAlert.__name__}", request.user.profile, submission)
        return redirect(competition.getLink(alert=Message.PARTICIPATION_CONFIRMED))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='5/m', block=True, method=(Code.POST))
def invite(request: WSGIRequest, subID: UUID) -> JsonResponse:
    """To invite a member in existing submission, relation to be confirmed via mail link.

    Args:
        request (WSGIRequest): The request object.
        subID (UUID): The submission UUID

    Returns:
        JsonResponse: response with Code.OK if invitation is sent successfully, Code.NO if not.
    """
    try:
        userID = str(request.POST.get('userID', '')).strip().lower()
        if not userID or userID == 'None':
            return respondJson(Code.NO, error=Message.INVALID_ID)
        submission = Submission.objects.get(
            id=subID, members=request.user.profile, submitted=False)
        SubmissionParticipant.objects.get(
            submission=submission, profile=request.user.profile, confirmed=True)
        if request.user.email.lower() == userID or str(request.user.profile.ghID()).lower() == userID or (userID in request.user.emails()):
            return respondJson(Code.NO, error=Message.ALREADY_PARTICIPATING)
        person = Profile.objects.filter(Q(user__email__iexact=userID) | Q(githubID__iexact=userID) | Q(nickname__iexact=userID), Q(
            is_active=True, suspended=False, to_be_zombie=False)).first()
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
                raise ObjectDoesNotExist('inactive:', submission.competition)
            if submission.competition.isJudge(person) or submission.competition.isModerator(person):
                return respondJson(Code.NO, error=Message.USER_PARTICIPANT_OR_INVITED)
            submission.members.add(person)
            addMethodToAsyncQueue(
                f'{APPNAME}.mailers.{participantInviteAlert.__name__}', person, request.user.profile, submission)
            return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_GET
def invitation(request: WSGIRequest, subID: UUID, userID: UUID) -> HttpResponse:
    """To render invitation action page for invitee of a submission.

    Args:
        request (WSGIRequest): The request object.
        subID (UUID): The submission UUID
        userID (UUID): The invitee user UUID

    Raises:
        Http404: If Submission is not found or competition is not active, or requesting user is not the invitee,
            or not allowed to participate

    Returns:
        HttpResponseRedirect: redirect to competition profile page if invitation doesn't exist,
            or if user is not invitee, or if user is already participant
        HttpResponse: renders text/html page of invitation if user is a valid invitee
    """
    try:
        if request.user.getID() != userID:
            raise ObjectDoesNotExist(userID)
        submission = Submission.objects.get(
            id=subID, submitted=False, members=request.user.profile)
        if not submission.competition.isActive():
            raise ObjectDoesNotExist(
                'inactive competition invite render', submission, request.user)
        if not submission.competition.isAllowedToParticipate(request.user.profile):
            raise ObjectDoesNotExist(
                'not allowed to part invite render', submission, request.user)
        try:
            SubmissionParticipant.objects.get(
                submission=submission, profile=request.user.profile, confirmed=False)
            return renderer(request, Template.Compete.INVITATION, dict(submission=submission))
        except ObjectDoesNotExist:
            return redirect(submission.competition.getLink(error=Message.INVITE_NOTEXIST))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
def inviteAction(request: WSGIRequest, subID: UUID, userID: UUID, action: str) -> HttpResponse:
    """To accpet/decline participation invitation, by invitee for a submission of a competition.

    Args:
        request (WSGIRequest): The request object.
        subID (UUID): The submission UUID
        userID (UUID): The invitee user UUID
        action (str): The action to be performed (main.strings.Action.ACCEPT/main.strings.Action.DECLINE)

    Raises:
        Http404: If Submission is not found or competition is not active, or requesting user is not the invitee,
            or not allowed to participate, or action is invalid

    Returns:
        HttpResponse: renders text/html page of invitation with proceed action, if user is a valid invitee and action is valid
    """
    try:
        if request.user.getID() != userID:
            raise ObjectDoesNotExist(userID)
        submission = Submission.objects.get(
            id=subID, submitted=False, members=request.user.profile)
        if not submission.competition.isActive():
            raise ObjectDoesNotExist('inactive competition invite action')
        if not submission.competition.isAllowedToParticipate(request.user.profile):
            raise ObjectDoesNotExist(request.user.profile)
        if action == Action.DECLINE:
            SubmissionParticipant.objects.filter(
                submission=submission, profile=request.user.profile, confirmed=False).delete()
            return renderer(request, Template.Compete.INVITATION, dict(submission=submission, declined=True))
        elif action == Action.ACCEPT:
            SubmissionParticipant.objects.filter(
                submission=submission, profile=request.user.profile, confirmed=False).update(confirmed=True, confirmed_on=timezone.now())
            request.user.profile.increaseXP(by=4)
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{participantWelcomeAlert.__name__}", request.user.profile, submission)
            return renderer(request, Template.Compete.INVITATION, dict(submission=submission, accepted=True))
        else:
            raise ObjectDoesNotExist(action)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@decode_JSON
def removeMember(request: WSGIRequest, subID: UUID, userID: UUID) -> HttpResponse:
    """To remove member or withdraw participation from submission of a competition.

    Args:
        request (WSGIRequest): The request object.
        subID (UUID): The submission UUID
        userID (UUID): The member user UUID

    Raises:
        Http404: If Submission is not found or competition is not active, or member is not valid.


    Returns:
        HttpResponseRedirect: redirect to competition profile page if member is removed successfully
        JsonResponse: response main.strings.Code.OK if member is removed successfully, else main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        member = request.user.profile if request.user.getID(
        ) == userID else Profile.objects.get(user__id=userID)
        submission = Submission.objects.get(
            id=subID, members=member, submitted=False, competition__resultDeclared=False)
        SubmissionParticipant.objects.get(
            submission=submission, profile=request.user.profile, confirmed=True)
        if not submission.competition.isActive():
            raise InactiveCompetitionError(
                submission.competition, subID, userID)

        conf = SubmissionParticipant.objects.filter(
            profile=member, submission=submission, confirmed=True).first()
        submission.members.remove(member)
        if submission.totalActiveMembers() == 0:
            submission.delete()
        elif submission.free_project and submission.free_project.creator == member:
            submission.free_project = None
            submission.save()
        if conf:
            member.decreaseXP(by=5)
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{participationWithdrawnAlert.__name__}", member, submission)
        if json_body:
            return respondJson(Code.OK, message=(Message.PARTICIPATION_WITHDRAWN if request.user.profile == member else Message.MEMBER_REMOVED))
        return redirect(submission.competition.getLink(alert=f"{Message.PARTICIPATION_WITHDRAWN if request.user.profile == member else Message.MEMBER_REMOVED}"))
    except (InactiveCompetitionError, ObjectDoesNotExist) as c:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(c)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='5/s', block=True, method=(Code.POST))
def save(request: WSGIRequest, compID: UUID, subID: UUID) -> HttpResponse:
    """To save/update a submission of a competition. (Not the final submission)

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID
        subID (UUID): The submission UUID

    Raises:
        Http404: If Submission is not found or competition is not active, or user is not a participant.

    Returns:
        HttpResponseRedirect: redirect to competition profile page if submission is saved successfully
        JsonResponse: response main.strings.Code.OK if submission is saved successfully, else main.strings.Code.NO
    """

    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        now = timezone.now()
        subm = Submission.objects.get(id=subID, competition__id=compID,
                                      submitted=False, competition__startAt__lt=now,
                                      competition__endAt__gte=now, competition__resultDeclared=False,
                                      members=request.user.profile,
                                      )
        if not subm.competition.isAllowedToParticipate(request.user.profile):
            raise ObjectDoesNotExist('not allowed to part save subm')
        fprojID = request.POST['submissionfreeproject']
        if fprojID == Action.REMOVE:
            subm.free_project = None
        else:
            subm.free_project = FreeProject.objects.get(
                id=fprojID, creator=request.user.profile, suspended=False, trashed=False, createdOn__gte=subm.competition.startAt)
        subm.modifiedOn = now
        subm.save()
        if json_body:
            return respondJson(Code.OK)
        return redirect(subm.competition.getLink(alert=Message.SAVED))
    except (ObjectDoesNotExist, KeyError) as o:
        if json_body:
            return respondJson(Code.NO)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO)
        raise Http404(e)


@normal_profile_required
@require_JSON
def finalSubmit(request: WSGIRequest, compID: UUID, subID: UUID) -> JsonResponse:
    """To permanently submit the existing saved unsubmitted submission of a competition.
    Late submission is allowed unless the copmetition has been moderated.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID
        subID (UUID): The submission UUID

    Returns:
        JsonResponse: response main.strings.Code.OK if submission is submitted successfully, else main.strings.Code.NO
    """
    try:
        now = timezone.now()
        submission = Submission.objects.get(
            id=subID, competition__id=compID, competition__resultDeclared=False, members=request.user.profile, submitted=False)
        message = Message.SUBMITTED_SUCCESS
        if submission.isInvitee(request.user.profile):
            raise ObjectDoesNotExist(
                'unconfirmed participant', submission, request.user)
        if not submission.competition.isAllowedToParticipate(request.user.profile):
            raise ObjectDoesNotExist(
                'not allowed to participate', submission, request.user)
        if not submission.free_project:
            raise ObjectDoesNotExist(
                'no submission made', submission, request.user)
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
            if submission.late:
                member.increaseXP(by=1)
            else:
                member.increaseXP(by=2)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{submissionConfirmedAlert.__name__}", submission)
        return respondJson(Code.OK, message=message)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@mentor_only
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def submitPoints(request: WSGIRequest, compID: UUID) -> JsonResponse:
    """To submit their markings of all submissions of a competition by judge (mentor) of a competition.
    Only after the competition has been moderated, a judge can submit their markings.
    Also allotes topic XPs to the judge.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID.

        request.POST.submissions (dict): A list of submission dicts, containing:
            subID: submission UUID
            topics: list of topic dicts, containing:
                topicID: topic UUID
                points: points awarded for the topic to the submission

    Returns:
        JsonResponse: response main.strings.Code.OK if points are alloted successfully, else main.strings.Code.NO
    """
    try:
        subs = request.POST.get('submissions', None)
        if not subs:
            return respondJson(Code.NO, error=Message.SUBMISSION_MARKING_INVALID)

        submissions = Submission.objects.filter(competition__id=compID, competition__judges=request.user.profile,
                                                competition__resultDeclared=False, competition__endAt__lt=timezone.now(), valid=True).order_by('submitOn')
        competition = submissions.first().competition

        if competition.allSubmissionsMarkedByJudge(judge=request.user.profile):
            raise ObjectDoesNotExist(
                'already submitted points',  competition, request.user)
        if competition.isAllowedToParticipate(request.user.profile):
            raise ObjectDoesNotExist(
                'allowed to participate!', competition, request.user)

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

        """
        The structure of modifiedTops is:
        {
            '<topicID>': [
                {
                    '<subID>': <points>
                },
                ...
            ],
            ...
        }
        i.e. A dict with topic IDs as the keys, and the value of each is a 
        list of dicts having submission IDs as keys and their points as their values.
        """

        topicpointsList = []
        for topic in topics:
            subspointslist = modifiedTops[str(topic.getID())]
            for sub in subspointslist:
                point = None
                submission = None
                for subm in submissions:
                    if str(subm.getID()) in sub.keys():
                        submission = subm
                        point = int(sub[str(subm.getID())])
                        break
                if point == None or submission == None:
                    raise Exception(sub, topic, request.user, competition)
                else:
                    topicpointsList.append(SubmissionTopicPoint(
                        submission=submission,
                        topic=topic,
                        judge=request.user.profile,
                        points=point
                    ))

        _ = SubmissionTopicPoint.objects.bulk_create(
            topicpointsList)
        addMethodToAsyncQueue(
            f"{APPNAME}.mailers.{submissionsJudgedAlert.__name__}", competition, request.user.profile)

        judgeXP = len(submissions)//(len(topics)+1)
        request.user.profile.increaseBulkTopicPoints(
            topics=topics, by=judgeXP, reason=f"Judged submissions of {competition.title}")
        request.user.profile.increaseXP(by=judgeXP)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, KeyError, ValueError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@manager_only
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def declareResults(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """
    To declare results by the manager after markings of all submissions by all judges have been completed.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID.

    Raises:
        Http404: If the competition is not valid, or not ready to have the results declared.

    Returns:
        HttpResponseRedirect: Redirects to the management competition view.
    """
    try:
        comp = Competition.objects.get(
            id=compID, endAt__lt=timezone.now(), resultDeclared=False, creator=request.user.profile, is_draft=False)

        if comp.isAllowedToParticipate(request.user.profile):
            raise ObjectDoesNotExist(
                'allowed to participate!', comp, request.user)

        if not (comp.moderated() and comp.allSubmissionsMarked()):
            return redirect(comp.getManagementLink(error=Message.INVALID_REQUEST))
        taskKey = comp.CACHE_KEYS.result_declaration_task
        task = cache.get(taskKey, None)
        if task == Message.RESULT_DECLARING:
            return redirect(comp.getManagementLink(error=Message.RESULT_DECLARING))
        cache.set(taskKey, Message.RESULT_DECLARING, None)
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{DeclareResults.__name__}", comp)
        return redirect(comp.getManagementLink(alert=Message.RESULT_DECLARING))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def claimXP(request: WSGIRequest, compID: UUID, subID: UUID) -> HttpResponse:
    """To claim XP from competition by results declared submission's participant.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID.
        subID (UUID): The submission UUID.

    Raises:
        Http404: If the competition is not valid, or the submission is not valid,
            or XP has already been claimed.

    Returns:
        HttpResponsRedirect: Redirects to the competition view.
    """

    try:
        result = Result.objects.get(submission__competition__id=compID,
                                    submission__id=subID, submission__members=request.user.profile)
        if result.xpclaimers.filter(user=request.user).exists():
            raise ObjectDoesNotExist(request.user)
        profile = request.user.profile
        topicpoints = SubmissionTopicPoint.objects.filter(
            submission=result.submission).values('topic').annotate(points=Sum('points'))
        topicpointsIDs = []
        for topicpoint in topicpoints:
            topicpointsIDs.append(topicpoint['topic'])
        topics = Topic.objects.filter(id__in=topicpointsIDs)
        competition = result.submission.competition
        profile.increaseXP(by=(result.points)//(len(topicpointsIDs)+1),
                           reason=f"Claimed XP from {competition.title}")
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
                    profiletopic.increasePoints(
                        by=topicpoint['points'], notify=False, reason=f"Claimed XP from {competition.title}")
                    break
        result.xpclaimers.add(profile)
        return redirect(competition.getLink(alert=Message.XP_ADDED))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_JSON
def getTopicScores(request: WSGIRequest, resID: UUID) -> JsonResponse:
    """To get the scores of a result submission against all topics of the competition

    Args:
        request (WSGIRequest): The request object.
        resID (UUID): The result UUID.

    Returns:
        JsonResponse: responds main.strings.Code.OK and the scores of the result submission against all topics of the competition,
            if valid request, else main.strings.Code.NO
    """
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
    except ObjectDoesNotExist:
        return respondJson(Code.NO)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@require_GET
def certificateIndex(request: WSGIRequest) -> HttpResponse:
    """Certfiicate homepage.

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: renders the text/html certificate index page.
    """
    return renderer(request, Template.Compete.CERT_INDEX)


@ratelimit(key='user_or_ip', rate='2/s', block=True, method=(Code.POST))
def certificateVerify(request: WSGIRequest) -> HttpResponse:
    """To verify a certificate.
    Accpets certID to verify via both GET and POST methods.

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: Redirects to the certificate view, if valid certificate, else redirects to the certificate index page.
    """
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
    except ObjectDoesNotExist as o:
        return respondRedirect(APPNAME, f"{URL.Compete.CERT_INDEX}?certID={certID}", error=Message.CERT_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, f"{URL.Compete.CERT_INDEX}?certID={certID}", error=Message.CERT_NOT_FOUND)


@require_GET
def certificate(request: WSGIRequest, resID: UUID, userID: UUID) -> HttpResponse:
    """To render a participant's valid certificate view.
    Note that this will render the certificate view even if the certificate file is not yet generated,
    but the only when the reqeusted result ID is valid.

    Args:
        request (WSGIRequest): The request object.
        resID (UUID): The result UUID.
        userID (UUID): The certificate user UUID.

    Raises:
        Http404: If the result is not valid, or the request is not valid.

    Returns:
        HttpResponse: renders text/html certificate view (with/without certificate image/pdf/download URL).
    """
    try:
        if request.user.is_authenticated and request.user.getID() == userID:
            self = True
            member = request.user.profile
        else:
            self = False
            member = Profile.objects.get(
                user__id=userID, suspended=False, to_be_zombie=False)

        if request.user.is_authenticated and member.isBlocked(request.user):
            raise ObjectDoesNotExist(request.user)

        result = Result.objects.get(id=resID, submission__members=member)

        partcert = ParticipantCertificate.objects.filter(
            result__id=resID, profile=member).first()

        certpath = False if not partcert else partcert.getCertImage if partcert.certificate else False
        certID = False if not partcert else partcert.get_id
        return renderer(request, Template.Compete.CERT_CERTIFICATE, dict(result=result, member=member, certpath=certpath, self=self, certID=certID))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_GET
def appCertificate(request: WSGIRequest, compID: UUID, userID: UUID) -> HttpResponse:
    """To render a appreciant's valid certificate view.
    Note that this will render the certificate view even if the certificate file is not yet generated,
    but the only when the reqeusted cometition ID is valid.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID.
        userID (UUID): The certificate user UUID.

    Raises:
        Http404: If the competition is not valid, or the request is not valid.

    Returns:
        HttpResponse: renders text/html certificate view (with/without certificate image/pdf/download URL).
    """
    try:
        if request.user.is_authenticated and request.user.getID() == userID:
            self = True
            person = request.user.profile
        else:
            self = False
            person = Profile.objects.get(
                user__id=userID, suspended=False, to_be_zombie=False)

        if request.user.is_authenticated and person.isBlocked(request.user):
            raise ObjectDoesNotExist(request.user)

        appcert = AppreciationCertificate.objects.filter(
            competition__id=compID, appreciatee=person).first()

        certpath = False if not appcert else appcert.getCertImage if appcert.certificate else False
        certID = False if not appcert else appcert.get_id
        if appcert:
            compete = appcert.competition
        else:
            compete = Competition.objects.get(id=compID, is_draft=False)
        return renderer(request, Template.Compete.CERT_APPCERTIFICATE, dict(compete=compete, appcert=appcert, person=person, certpath=certpath, self=self, certID=certID))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@manager_only
@require_POST
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def generateCertificates(request: WSGIRequest, compID: UUID) -> HttpResponse:
    """To create a task to be queued to generate certificates for a competition,
        if the competition's result has been declared, by the manager.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID.

    Raises:
        Http404: If the competition is not valid, or the request is not valid.

    Returns:
        HttpResponseServerError: If request & competition is valid, but something went wrong.
        HttpResponseRedirect: Redirects to the management's competition page after task is successfully queued.
    """
    try:
        competition = Competition.objects.get(
            id=compID, creator=request.user.profile, resultDeclared=True, is_draft=False)
        if not (competition.resultDeclared and competition.allResultsDeclared()):
            return redirect(competition.getManagementLink(alert=Message.RESULT_NOT_DECLARED))
        if competition.certificatesGenerated():
            return redirect(competition.getManagementLink(alert=Message.CERTS_GENERATED))
        taskKey = competition.CACHE_KEYS.certificates_allotment_task
        if cache.get(taskKey) == Message.CERTS_GENERATING:
            return redirect(competition.getManagementLink(alert=Message.CERTS_GENERATING))
        doneresultIDs = ParticipantCertificate.objects.filter(
            result__competition=competition).values_list("result__id", flat=True)
        remainingresults = Result.objects.filter(
            competition=competition).exclude(id__in=list(doneresultIDs))
        cache.set(taskKey, Message.CERTS_GENERATING, settings.CACHE_ETERNAL)
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{AllotCompetitionCertificates.__name__}", remainingresults, competition)
        return redirect(competition.getManagementLink(alert=Message.CERTS_GENERATING))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        return HttpResponseServerError(e)


@normal_profile_required
@require_GET
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def downloadCertificate(request: WSGIRequest, resID: UUID, userID: UUID) -> HttpResponse:
    """To respond with a participant's certificate file.

    Args:
        request (WSGIRequest): The request object.
        resID (UUID): The result UUID.
        userID (UUID): The certificate user UUID.

    Raises:
        Http404: If the certificate is not yet generated, or the request is not valid.

    Returns:
        HttpResponse: responds with application/pdf certificate file.
    """
    try:
        if request.user.getID() == userID:
            member = request.user.profile
        else:
            raise ObjectDoesNotExist(userID)
        partcert = ParticipantCertificate.objects.get(
            result__id=resID, profile=member)
        if not partcert.certificate:
            raise ObjectDoesNotExist("Certificate not yet present!", partcert)
        file_path = os_path.join(
            settings.MEDIA_ROOT, str(partcert.certificate))
        if os_path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(
                    fh.read(), content_type=Code.APPLICATION_PDF)
                response['Content-Disposition'] = 'inline; filename=' + \
                    os_path.basename(file_path)
                return response
        raise ObjectDoesNotExist(file_path)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_GET
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def appDownloadCertificate(request: WSGIRequest, compID: UUID, userID: UUID) -> HttpResponse:
    """To respond with a appreciant's certificate file.

    Args:
        request (WSGIRequest): The request object.
        compID (UUID): The competition UUID.
        userID (UUID): The certificate user UUID.

    Raises:
        Http404: If the certificate is not yet generated, or the request is not valid.

    Returns:
        HttpResponse: responds with application/pdf certificate file.
    """
    try:
        if request.user.getID() == userID:
            person = request.user.profile
        else:
            raise ObjectDoesNotExist(userID)
        appcert = AppreciationCertificate.objects.get(
            competition__id=compID, appreciatee=person)
        if not appcert.certificate:
            raise ObjectDoesNotExist("Certificate not yet present!", appcert)

        file_path = os_path.join(settings.MEDIA_ROOT, str(appcert.certificate))
        if os_path.exists(file_path):
            with open(file_path, 'rb') as fh:
                response = HttpResponse(
                    fh.read(), content_type=Code.APPLICATION_PDF)
                response['Content-Disposition'] = 'inline; filename=' + \
                    os_path.basename(file_path)
                return response
        raise ObjectDoesNotExist(file_path)
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def browseSearch(request: WSGIRequest) -> HttpResponse:
    """To respond with a list of competitions (html/json) based on the search query.

    Args:
        request (WSGIRequest): The request object.

    Raises:
        Http404: If the request is not valid, or something went wrong.

    Returns:
        HttpResponse: responds with text/html main.strings.Template.Compete.BROWSE_SEARCH file with competitions data.
        JsonResponse: responds main.strings.Code.OK with list of competitions.
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ''))
        limit = request.GET.get('limit', request.POST.get('limit', 10))

        cachekey = f'compete_browse_search_{query}{request.LANGUAGE_CODE}'
        if request.user.is_authenticated:
            cachekey = f"{cachekey}{request.user.id}"

        competitions = cache.get(cachekey, [])

        if not len(competitions):
            specials = ('topic:', 'manager:', 'judge:', 'status:')
            pquery = None
            dbquery = Q()
            invalidQuery = False
            if query.startswith(specials):
                def specquerieslist(q):
                    return [Q(topics__name__iexact=q), Q(creator__user__first_name__istartswith=q), Q(judges__user__first_name__istartswith=q, resultDeclared=True), Q()]
                commaparts = query.split(",")
                for cpart in commaparts:
                    if cpart.strip().lower().startswith(specials):
                        special, specialq = cpart.split(':')
                        if special.strip().lower() == 'status':
                            status = specialq.strip().lower()

                            if status == Code.ACTIVE:
                                dbquery = Q(
                                    dbquery, startAt__lte=timezone.now(), endAt__gte=timezone.now())
                            if status == Code.HISTORY:
                                dbquery = Q(dbquery, endAt__lt=timezone.now())
                            if status == Code.UPCOMING:
                                dbquery = Q(
                                    dbquery, startAt__gt=timezone.now())
                            if status not in [Code.ACTIVE, Code.HISTORY, Code.UPCOMING]:
                                invalidQuery = True
                                break
                        else:
                            dbquery = Q(dbquery, specquerieslist(specialq.strip())[
                                        list(specials).index(f"{special.strip()}:")])
                    else:
                        pquery = cpart.strip()
                        break
            else:
                pquery = query

            if pquery and not invalidQuery:
                dbquery = Q(dbquery, Q(
                    Q(title__istartswith=pquery)
                    | Q(tagline__istartswith=pquery)
                    | Q(nickname__istartswith=pquery)
                    | Q(shortdescription__istartswith=pquery)
                    | Q(topics__name__istartswith=pquery)
                    | Q(title__icontains=pquery)
                    | Q(nickname__icontains=pquery)
                    | Q(tagline__icontains=pquery)
                    | Q(shortdescription__icontains=pquery)
                    | Q(creator__user__first_name__istartswith=pquery)
                    | Q(creator__user__last_name__istartswith=pquery)
                    | Q(creator__user__email__istartswith=pquery)
                    | Q(creator__nickname__istartswith=pquery)
                    | Q(qualifier__title__istartswith=pquery)
                    | Q(qualifier__tagline__istartswith=pquery)
                    | Q(qualifier__topics__name__istartswith=pquery)
                ))

            if not invalidQuery:
                competitions = Competition.objects.filter(dbquery).exclude(
                    hidden=True).exclude(is_draft=True).distinct()[:limit]
                if len(competitions):
                    cache.set(cachekey, competitions, settings.CACHE_SHORT)

        if json_body:
            return respondJson(Code.OK, dict(
                competitions=list(map(lambda c: dict(
                    id=c.get_id,
                    title=c.title,
                    tagline=c.tagline,
                    shortdescription=c.shortdescription,
                    manager=c.creator.get_name,
                    manager_link=c.creator.get_link,
                    manager_dp=c.creator.get_dp,
                    isUpcoming=c.isUpcoming(),
                    isActive=c.isActive(),
                    isHistory=c.isHistory(),
                    resultDeclared=c.resultDeclared,
                    banner_abs=c.get_banner_abs,
                    banner=c.get_banner,
                    url=c.get_link,
                ), competitions)),
                query=query
            ))
        return rendererstrResponse(request, Template.Compete.BROWSE_SEARCH, dict(competitions=competitions, query=query))
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)
