from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import Http404, HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST
from main.decorators import manager_only, require_JSON_body
from main.methods import base64ToImageFile, respondRedirect, errorLog, respondJson
from main.strings import COMPETE, URL, Message, Code, Template
from moderation.methods import assignModeratorToObject, getModeratorToAssignModeration
from compete.models import Competition
from projects.models import Category, Tag
from people.models import Topic, Profile
from moderation.models import Moderation
from projects.methods import addTagToDatabase, addCategoryToDatabase
from people.methods import addTopicToDatabase
from main.env import BOTMAIL
from .methods import renderer, createCompetition, rendererstr
from .models import Report, Feedback
from .apps import APPNAME


@manager_only
@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Management.INDEX)


@manager_only
@require_GET
def community(request: WSGIRequest):
    return renderer(request, Template.Management.COMMUNITY_INDEX)


@manager_only
@require_GET
def moderators(request: WSGIRequest):
    moderators = Profile.objects.exclude(user__email__in=[request.user.email,BOTMAIL]).filter(is_moderator=True,to_be_zombie=False)
    profiles = Profile.objects.exclude(user__email__in=[request.user.email,BOTMAIL]).filter(is_moderator=False,to_be_zombie=False, is_active=True).order_by('-xp')[0:10]
    return renderer(request, Template.Management.COMMUNITY_MODERATORS, dict(moderators=moderators,profiles=profiles))


@manager_only
@require_JSON_body
def searchEligibleModerator(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        profile = Profile.objects.exclude(user__email__in=[request.user.email,BOTMAIL]).filter(Q(Q(is_active=True, suspended=False, to_be_zombie=False, is_moderator=False), Q(
            user__email__startswith=query) | Q(user__first_name__startswith=query) | Q(githubID__startswith=query))).first()
        if profile.isBlocked(request.user):
            raise Exception()
        return respondJson(Code.OK, dict(mod=dict(
            id=profile.user.id,
            userID=profile.getUserID(),
            name=profile.getName(),
            email=profile.getEmail(),
            url=profile.getLink(),
            dp=profile.getDP(),
        )))
    except Exception as e:
        print(e)
        return respondJson(Code.NO)

@manager_only
@require_JSON_body
def removeModerator(request: WSGIRequest):
    try:
        modID = request.POST.get('modID',None)
        if not modID or modID == request.user.get_id:
            return respondJson(Code.NO)
        moderator = Profile.objects.filter(user__id=modID, is_moderator=True).update(is_moderator=False)
        if moderator == 0:
            return respondJson(Code.NO)
        for mod in Moderation.objects.filter(moderator__user__id=modID, resolved=False):
            moderator = getModeratorToAssignModeration(mod.type,mod.object, ignoreModProfiles=[mod.moderator])
            if moderator:
                mod.moderator = moderator
                mod.save()
        return respondJson(Code.OK)
    except Exception as e:
        print(e)
        return respondJson(Code.NO, error=e)

@manager_only
@require_JSON_body
def addModerator(request: WSGIRequest):
    try:
        userID = request.POST.get('userID',None)
        if not userID or userID == request.user.get_id:
            return respondJson(Code.NO)

        user = Profile.objects.filter(user__id=userID, is_moderator=False, suspended=False, to_be_zombie=False).update(is_moderator=True)
        if user == 0:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except Exception as e:
        return respondJson(Code.NO, error=e)


@manager_only
@require_GET
def labels(request: WSGIRequest):
    categories = Category.objects.filter()
    topics = Topic.objects.filter()
    return renderer(request, Template.Management.COMMUNITY_LABELS, dict(
        categories=categories,
        topics=topics
    ))


@manager_only
@require_GET
def labelType(request: WSGIRequest, type: str):
    try:
        if type == Code.TOPIC:
            topics = Topic.objects.filter()
            return rendererstr(request, Template.Management.COMMUNITY_LABELS_TOPICS, dict(topics=topics))
        if type == Code.CATEGORY:
            categories = Category.objects.filter()
            return rendererstr(request, Template.Management.COMMUNITY_LABELS_CATEGORIES, dict(categories=categories))
        if type == Code.TAG:
            tags = Tag.objects.filter()
            return rendererstr(request, Template.Management.COMMUNITY_LABELS_TAGS, dict(tags=tags))
        raise Exception('Invalid label')
    except:
        raise Http404()


@manager_only
@require_GET
def label(request: WSGIRequest, type: str, labelID: UUID):
    try:
        if type == Code.TOPIC:
            topic = Topic.objects.get(id=labelID)
            return renderer(request, Template.Management.COMMUNITY_TOPIC, dict(topic=topic))
        if type == Code.CATEGORY:
            category = Category.objects.get(id=labelID)
            return renderer(request, Template.Management.COMMUNITY_CATEGORY, dict(category=category))
        raise Exception('Invalid label')
    except:
        raise Http404()

@manager_only
@require_JSON_body
def labelCreate(request: WSGIRequest, type: str):
    try:
        name = request.POST['name']
        if type == Code.TOPIC:
            label = addTopicToDatabase(name)
        elif type == Code.CATEGORY:
            label = addCategoryToDatabase(name)
        elif type == Code.TAG:
            label = addTagToDatabase(name)
        else:
            return respondJson(Code.NO)
        return respondJson(Code.OK, dict(label=dict(id=label.get_id,name=label.name)))
    except:
        return respondJson(Code.NO)
    
@manager_only
@require_JSON_body
def labelUpdate(request: WSGIRequest, type: str, labelID:UUID):
    try:
        if type == Code.TAG:
            name = request.POST['name']
            tag = Tag.objects.filter(id=labelID).update(name=name)
        elif type == Code.TOPIC:
            topic = Topic.objects.filter(id=labelID).update()
        elif type == Code.CATEGORY:
            category = Category.objects.filter(id=labelID).update()
        else:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except:
        return respondJson(Code.NO)
    
    

@manager_only
@require_JSON_body
def labelDelete(request: WSGIRequest, type: str, labelID:UUID):
    try:
        if type == Code.TOPIC:
            topic = Topic.objects.get(id=labelID)
            if topic.isDeletable:
                topic.delete()
        elif type == Code.CATEGORY:
            category = Category.objects.get(id=labelID)
            if category.isDeletable:
                category.delete()
        elif type == Code.TAG:
            tags = Tag.objects.filter(id=labelID).delete()
        else:
            return respondJson(Code.NO)
        return respondJson(Code.OK)
    except:
        return respondJson(Code.NO)
    

@manager_only
@require_GET
def competitions(request: WSGIRequest) -> HttpResponse:
    try:
        competes = Competition.objects.filter()
        return renderer(request, Template.Management.COMP_INDEX, dict(competes=competes))
    except:
        raise Http404()


@manager_only
@require_GET
def competition(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        compete = Competition.objects.get(id=compID)
        return renderer(request, Template.Management.COMP_COMPETE, dict(
            compete=compete,
            iscreator=(compete.creator == request.user.profile)
        ))
    except Exception as e:
        print(e)
        raise Http404()


@manager_only
@require_JSON_body
def searchTopic(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        topic = Topic.objects.filter(name__istartswith=query.capitalize()).first()
        return respondJson(Code.OK, dict(topic=dict(
            id=topic.id,
            name=topic.name
        )))
    except Exception as e:
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def searchJudge(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        profile = Profile.objects.exclude(user__email__in=[request.user.email,BOTMAIL]).filter(Q(Q(is_active=True, suspended=False, to_be_zombie=False), Q(
            user__email__startswith=query) | Q(user__first_name__startswith=query) | Q(githubID__startswith=query))).first()
        if profile.isBlocked(request.user):
            raise Exception()
        return respondJson(Code.OK, dict(judge=dict(
            id=profile.user.id,
            name=profile.getName()
        )))
    except Exception as e:
        return respondJson(Code.NO)


@manager_only
@require_JSON_body
def searchModerator(request: WSGIRequest) -> JsonResponse:
    try:
        query = request.POST.get('query', None)
        if not query or not str(query).strip():
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        profile = Profile.objects.exclude(user__email__in=[request.user.email,BOTMAIL]).filter(Q(Q(is_active=True, suspended=False, to_be_zombie=False, is_moderator=True), Q(
            user__email__startswith=query) | Q(user__first_name__startswith=query) | Q(githubID__startswith=query))).first()
        if profile.isBlocked(request.user):
            raise Exception()
        return respondJson(Code.OK, dict(mod=dict(
            id=profile.user.id,
            userID=profile.getUserID(),
            name=profile.getName(),
            email=profile.getEmail(),
            url=profile.getLink(),
            dp=profile.getDP(),
        )))
    except Exception as e:
        return respondJson(Code.NO)
    


@manager_only
@require_GET
def createCompete(request: WSGIRequest) -> HttpResponse:
    return renderer(request, Template.Management.COMP_CREATE)


@manager_only
@require_POST
def submitCompetition(request) -> HttpResponse:
    try:
        title = str(request.POST["comptitle"]).strip()
        tagline = str(request.POST["comptagline"]).strip()
        shortdesc = str(request.POST["compshortdesc"]).strip()
        desc = str(request.POST["compdesc"]).strip()
        modID = str(request.POST['compmodID']).strip()
        startAt = request.POST['compstartAt']
        endAt = request.POST['compendAt']
        eachTopicMaxPoint = int(request.POST['compeachTopicMaxPoint'])
        topicIDs = str(request.POST['comptopicIDs']
                       ).strip().strip(',').split(',')
        judgeIDs = str(request.POST['compjudgeIDs']
                       ).strip().strip(',').split(',')
        perks = [str(request.POST['compperk1']).strip(),
                 str(request.POST['compperk2']).strip(),
                 str(request.POST['compperk3']).strip()]
        taskSummary = str(request.POST['comptaskSummary']).strip()
        taskDetail = str(request.POST['comptaskDetail']).strip()
        taskSample = str(request.POST['comptaskSample']).strip()

        if not (title and
                tagline and
                shortdesc and
                desc and
                modID and
                startAt and
                endAt and
                eachTopicMaxPoint > 0 and
                len(topicIDs) > 0 and
                len(judgeIDs) > 0 and
                len(perks) > 2 and
                taskSummary and
                taskDetail and
                taskSample):
            raise Exception("Invalid details")

        if Competition.objects.filter(title__iexact=title).exists():
            return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.COMP_TITLE_EXISTS)

        compete = createCompetition(
            creator=request.user.profile,
            title=title,
            tagline=tagline,
            shortdescription=shortdesc,
            description=desc,
            perks=perks,
            startAt=startAt,
            endAt=endAt,
            eachTopicMaxPoint=eachTopicMaxPoint,
            topicIDs=topicIDs,
            judgeIDs=judgeIDs,
            taskSummary=taskSummary,
            taskDetail=taskDetail,
            taskSample=taskSample,
        )
        if not compete:
            raise Exception("Competition not created")
        try:
            bannerdata = request.POST['compbanner']
            bannerfile = base64ToImageFile(bannerdata)
            if bannerfile:
                compete.banner = bannerfile
            compete.save()
        except:
            pass

        mod = Profile.objects.get(user__id=modID, is_moderator=True, is_active=True, to_be_zombie=False, suspended=False)
        assigned = assignModeratorToObject(
            COMPETE, compete, mod, "Competition")
        if not assigned:
            return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.INVALID_MODERATOR)
        return respondRedirect(APPNAME, URL.Management.COMPETITIONS)
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, URL.Management.CREATE_COMP, error=Message.ERROR_OCCURRED)


@manager_only
@require_GET
def reportFeedbacks(request: WSGIRequest):
    reports = Report.objects.filter()
    feedbacks = Feedback.objects.filter()
    return renderer(request, Template.Management.REPORTFEED_INDEX, dict(
        reports=reports,
        feedbacks=feedbacks,
    ))


@manager_only
@require_GET
def reports(request: WSGIRequest):
    reports = Report.objects.filter()
    return rendererstr(request, Template.Management.REPORTFEED_REPORTS, dict(
        reports=reports
    ))


@require_JSON_body
def createReport(request: WSGIRequest) -> JsonResponse:
    email = request.POST.get('email', None)
    email = str(email).strip()
    reporter = None
    if email and str(email).strip():
        if request.user.is_authenticated and email == request.user.email:
            reporter = request.user.profile
        else:
            reporter = Profile.objects.filter(
                user__email__iexact=email).first()
    summary = request.POST.get('summary', '')
    detail = request.POST.get('detail', '')
    report = Report.objects.create(
        reporter=reporter, summary=summary, detail=detail)
    return respondJson(Code.OK if report else Code.NO, error=Message.ERROR_OCCURRED if not report else '')


@manager_only
@require_GET
def report(request: WSGIRequest, reportID: UUID):
    try:
        report = Report.objects.get(id=reportID)
        return renderer(request, Template.Management.REPORTFEED_REPORT, dict(report=report))
    except:
        raise Http404()


@manager_only
@require_GET
def feedbacks(request: WSGIRequest):
    feedbacks = Feedback.objects.filter()
    return rendererstr(request, Template.Management.REPORTFEED_FEEDBACKS, dict(
        feedbacks=feedbacks
    ))


@require_JSON_body
def createFeedback(request: WSGIRequest):
    email = request.POST.get('email', None)
    email = str(email).strip()
    feedbacker = None
    if email and str(email).strip():
        if request.user.is_authenticated and email == request.user.email:
            feedbacker = request.user.profile
        else:
            feedbacker = Profile.objects.filter(
                user__email__iexact=email).first()
    detail = request.POST.get('detail', '')
    feedback = Feedback.objects.create(feedbacker=feedbacker, detail=detail)
    return respondJson(Code.OK if feedback else Code.NO, error=Message.ERROR_OCCURRED if not feedback else '')


@manager_only
@require_GET
def feedback(request: WSGIRequest, feedID: UUID):
    try:
        feedback = Feedback.objects.get(id=feedID)
        return renderer(request, Template.Management.REPORTFEED_FEEDBACK, dict(feedback=feedback))
    except:
        raise Http404()
