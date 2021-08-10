from uuid import UUID
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import Http404, HttpResponse, JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET, require_POST
from main.decorators import manager_only, require_JSON_body
from main.methods import base64ToImageFile, respondRedirect, errorLog, respondJson
from main.strings import COMPETE, URL, Message, Code
from moderation.methods import assignModeratorToObject
from compete.models import Competition
from projects.models import Category
from people.models import Topic, Profile
from .methods import renderer, createCompetition, rendererstr
from .models import Report, Feedback
from .apps import APPNAME


@manager_only
@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    return renderer(request, 'index')


@manager_only
@require_GET
def community(request: WSGIRequest):
    return renderer(request, 'community/index')


@manager_only
@require_GET
def moderators(request: WSGIRequest):
    return renderer(request, 'community/moderators')


@manager_only
@require_GET
def labels(request: WSGIRequest):
    categories = Category.objects.filter()
    topics = Topic.objects.filter()
    return renderer(request, 'community/labels', dict(
        categories=categories,
        topics=topics
    ))


@manager_only
@require_GET
def label(request: WSGIRequest, type: str, labelID: UUID):
    try:
        if type == Code.TOPIC:
            topic = Topic.objects.get(id=labelID)
            return renderer(request, 'community/topic', dict(topic=topic))
        if type == Code.CATEGORY:
            category = Category.objects.get(id=labelID)
            return renderer(request, 'community/category', dict(category=category))
        else:
            raise Exception('Invalid label')
    except:
        raise Http404()


@manager_only
@require_GET
def topics(request: WSGIRequest):
    topics = Topic.objects.filter()
    return rendererstr(request, 'community/labels/topics', dict(topic=topics))


@manager_only
@require_GET
def categories(request: WSGIRequest):
    categories = Category.objects.filter()
    return rendererstr(request, 'community/labels/categories', dict(categories=categories),)


@manager_only
@require_GET
def competitions(request: WSGIRequest) -> HttpResponse:
    try:
        competes = Competition.objects.filter()
        return renderer(request, 'competition/index', dict(competes=competes))
    except:
        raise Http404()


@manager_only
@require_GET
def competition(request: WSGIRequest, compID: UUID) -> HttpResponse:
    try:
        compete = Competition.objects.get(id=compID)
        return renderer(request, 'competition/compete', dict(
            compete=compete,
            iscreator=(compete.creator == request.user.profile)
        ))
    except:
        raise Http404()


@manager_only
@require_JSON_body
def searchJudge(request: WSGIRequest) -> JsonResponse:
    query = request.POST.get('query', None)
    if not query or not str(query).strip():
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    profiles = Profile.objects.filter(Q(Q(is_active=True, suspended=False, is_zombie=False, to_be_zombie=False), Q(
        user__email__startswith=query) | Q(user__first_name__startswith=query) | Q(githubID__startswith=query)))[0:5]
    return respondJson(Code.OK, dict(profiles=profiles))

@manager_only
@require_JSON_body
def searchModerator(request: WSGIRequest) -> JsonResponse:
    query = request.POST.get('query', None)
    if not query or not str(query).strip():
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    profiles = Profile.objects.filter(Q(Q(is_active=True, suspended=False, is_zombie=False, to_be_zombie=False, is_moderator=True), Q(
        user__email__startswith=query) | Q(user__first_name__startswith=query) | Q(githubID__startswith=query)))[0:5]
    return respondJson(Code.OK, dict(profiles=profiles))

@manager_only
@require_GET
def createCompete(request: WSGIRequest) -> HttpResponse:
    fields = [dict(name="comptitle",
                   title="comptitle",
                   placeholder="comptitle"),
              dict(name="comptagline",
                   title="comptagline",
                   placeholder="comptagline"),
              dict(name="compshortdesc",
                   title="compshortdesc",
                   placeholder="compshortdesc"),
              dict(name="compdesc",
                   title="compdesc",
                   placeholder="compdesc"),
              dict(name="compmodID",
                   title="compmodID",
                   placeholder="compmodID"),
              dict(name="compstartAt",
                   title="compstartAt",
                   placeholder="compstartAt"),
              dict(name="compendAt",
                   title="compendAt",
                   placeholder="compendAt"),
              dict(name="compeachTopicMaxPoint",
                   title="compeachTopicMaxPoint",
                   placeholder="compeachTopicMaxPoint"),
              dict(name="comptopicIDs",
                   title="comptopicIDs",
                   placeholder="comptopicIDs"),
              dict(name="compjudgeIDs",
                   title="compjudgeIDs",
                   placeholder="compjudgeIDs"),
              dict(name="compperks",
                   title="compperks",
                   placeholder="compperks"),
              dict(name="comptaskSummary",
                   title="comptaskSummary",
                   placeholder="comptaskSummary"),
              dict(name="comptaskDetail",
                   title="comptaskDetail",
                   placeholder="comptaskDetail"),
              dict(name="comptaskSample",
                   title="comptaskSample",
                   placeholder="comptaskSample")]
    return renderer(request, 'competition/create', dict(fields=fields))


@manager_only
@require_POST
def submitCompetition(request) -> HttpResponse:
    try:
        title = str(request.POST["comptitle"]).strip()
        tagline = str(request.POST["comptagline"]).strip()
        shortdesc = str(request.POST["compshortdesc"]).strip()
        desc = str(request.POST["compdesc"]).strip()
        modID = str(request.POST['modID']).strip()
        startAt = request.POST['compstartAt']
        endAt = request.POST['compendAt']
        eachTopicMaxPoint = int(request.POST['compeachTopicMaxPoint'])
        topicIDs = str(request.POST['comptopicIDs']
                       ).strip().strip(',').split(',')
        judgeIDs = str(request.POST['compjudgeIDs']
                       ).strip().strip(',').split(',')
        perks = str(request.POST['compPerks']).strip().strip(';').split(';')
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

        mod = Profile.objects.get(user__id=modID, is_moderator=True, is_active=True,
                                  to_be_zombie=False, is_zombie=False, suspended=False)
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
    return renderer(request, 'reportFeed/index', dict(
        reports=reports,
        feedbacks=feedbacks,
    ))


@manager_only
@require_GET
def reports(request: WSGIRequest):
    reports = Report.objects.filter()
    return rendererstr(request, 'reportFeed/reports', dict(
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
        return renderer(request, 'reportFeed/report', dict(report=report))
    except:
        raise Http404()


@manager_only
@require_GET
def feedbacks(request: WSGIRequest):
    feedbacks = Feedback.objects.filter()
    return rendererstr(request, 'reportFeed/feedbacks', dict(
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
        return renderer(request, 'reportFeed/feedback', dict(feedback=feedback))
    except:
        raise Http404()
