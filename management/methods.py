from uuid import UUID
from compete.models import Competition, Perk
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http.response import HttpResponse
from main.bots import Discord
from main.methods import (addMethodToAsyncQueue, errorLog, renderString,
                          renderView)
from main.strings import Code, Message
from people.models import Profile, Topic
from projects.models import Category

from management.models import Management

from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Renderer for management views

    Args:
        request (WSGIRequest): The request object
        file (str): The file to render under templates/management, without extension
        data (dict, optional): The context data to pass to the file. Defaults to dict().

    Returns:
        HttpResponse: The rendered response with text/html file and data
    """
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """To return string based http response for management views

    Args:
        request (WSGIRequest): The request object
        file (str): The file to render under templates/management, without extension
        data (dict, optional): The context data to pass to the file. Defaults to dict().

    Returns:
        HttpResponse: The response with text/html content and data
    """
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def createCompetition(creator: Profile, title: str, tagline: str, shortdescription: str,
                      description: str, perks: list, startAt: str, endAt: str, eachTopicMaxPoint: int, topicIDs: list,
                      judgeIDs: list, taskSummary: str, taskDetail: str, taskSample: str, max_grouping: int,
                      reg_fee: float, fee_link: str, qualifier: Competition = None, qualifier_rank: int = 0
                      ) -> Competition:
    """Create a new competition, draft by default.

    Args:
        creator (Profile): The creator of the competition
        title (str): The title of the competition
        tagline (str): The tagline of the competition
        shortdescription (str): The short description of the competition
        description (str): The description of the competition
        perks (list<str>): The perks of the competition
        startAt (str): The start date of the competition
        endAt (str): The end date of the competition
        eachTopicMaxPoint (int): The max point of each topic
        topicIDs (list<UUID>): The topic IDs of the competition
        judgeIDs (list<UUID>): The judge IDs of the competition
        taskSummary (str): The task summary of the competition
        taskDetail (str): The task detail of the competition
        taskSample (str): The task sample of the competition
        max_grouping (int): The max grouping of the competition
        reg_fee (float): The registration fee of the competition
        fee_link (str): The link of the registration fee of the competition
        qualifier (Competition, optional): The qualifier of the competition. Defaults to None.
        qualifier_rank (int, optional): The rank of the qualifier. Defaults to 0.

    Returns:
        Competition: The created competition
        bool: False if failed to create a competition
    """
    compete = None
    try:
        if not creator.is_manager():
            raise Exception(f"Unauthorized manager")

        if len(perks) < 1:
            raise Exception(f"invalid perks {perks}")
        if startAt >= endAt:
            raise Exception(f"invalid timings")
        if eachTopicMaxPoint < 1:
            raise Exception(f"invalid eachTopicMaxPoint")
        if max_grouping < 1:
            raise Exception(f"invalid max_grouping")
        if reg_fee < 0:
            raise Exception(f"invalid reg_fee")

        compete = Competition.objects.create(
            creator=creator,
            title=title,
            tagline=tagline,
            shortdescription=shortdescription,
            description=description,
            taskSummary=taskSummary,
            taskDetail=taskDetail,
            taskSample=taskSample,
            startAt=startAt,
            endAt=endAt,
            eachTopicMaxPoint=eachTopicMaxPoint,
            max_grouping=max_grouping,
            reg_fee=reg_fee,
            fee_link=fee_link,
            resultDeclared=False,
            qualifier=qualifier,
            qualifier_rank=qualifier_rank
        )
        topics = Topic.objects.filter(id__in=topicIDs)
        if len(topics) < 1:
            raise ValueError(f"invalid topics", topics, compete)
        for topic in topics:
            compete.topics.add(topic)
        judges = Profile.objects.filter(
            suspended=False, is_active=True, to_be_zombie=False, user__id__in=judgeIDs)
        for judge in judges:
            if judge.isBlocked(creator.user):
                continue
            compete.judges.add(judge)
        if compete.totalJudges() < 1:
            raise ValueError(f"invalid judges", judges, compete)
        perkobjs = []
        for i, perk in enumerate(perks):
            if perk.strip() == "":
                continue
            perkobjs.append(Perk(
                competition=compete,
                name=perk,
                rank=(i+1)
            ))
        if len(perkobjs) < 1:
            raise ValueError(f"invalid judges", perkobjs, compete)
        Perk.objects.bulk_create(
            perkobjs, batch_size=100, ignore_conflicts=True)
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{setupCompetitionChannel.__name__}", compete)
        return compete
    except ValueError:
        pass
    except Exception as e:
        errorLog(e)
    if compete:
        compete.delete()
    return False


def setupCompetitionChannel(compete: Competition) -> str:
    """Setup a Discord channel for the competition

    Args:
        compete (Competition): The competition instance

    Returns:
        str: The discord channel ID
        bool: False if failed to create a channel
    """
    return Discord.create_channel(compete.get_nickname(), public=True, category="COMPETITIONS", message=f"Official discord channel for {compete.title} {compete.get_abs_link}")


def labelRenderData(request: WSGIRequest, type: str, labelID: UUID) -> dict:
    """Render data for individual label management views

    Args:
        request (WSGIRequest): The request object
        type (str): The type of the label
        labelID (UUID): The ID of the label

    Returns:
        dict: The context data
    """
    try:
        mgm:Management = request.user.profile.management()
        cacheKey = f"{APPNAME}_labelrenderdata_{type}_{labelID}_{mgm.id}"
        if type == Code.TOPIC:
            topic:Topic = cache.get(cacheKey, None)
            if not topic:
                topic:Topic = Topic.objects.filter(Q(id=labelID), Q(
                    Q(creator__in=mgm.people.all()) | Q(creator=request.user.profile))).first()
                if not topic:
                    return False
                cache.set(cacheKey, topic, settings.CACHE_MICRO)
            return dict(topic=topic)
        if type == Code.CATEGORY:
            category:Category = cache.get(cacheKey, None)
            if not category:
                category:Category = Category.objects.filter(Q(id=labelID), Q(
                    Q(creator__in=mgm.people.all()) | Q(creator=request.user.profile))).first()
                if not category:
                    return False
                cache.set(cacheKey, category, settings.CACHE_MICRO)
            return dict(category=category)
        return False
    except Exception as e:
        errorLog(e)
        return False


def competitionManagementRenderData(request: WSGIRequest, compID: UUID) -> dict:
    """Context data for competition management view

    Args:
        request (WSGIRequest): The request object
        compID (UUID): The ID of the competition

    Returns:
        dict: The context data
    """
    try:
        compete: Competition = Competition.objects.get(
            id=compID, creator=request.user.profile)
        resstatus: str = cache.get(compete.CACHE_KEYS.result_declaration_task)
        certstatus: str = cache.get(
            compete.CACHE_KEYS.certificates_allotment_task)
        return dict(
            compete=compete,
            iscreator=(compete.creator == request.user.profile),
            declaring=(resstatus == Message.RESULT_DECLARING),
            generating=(certstatus == Message.CERTS_GENERATING)
        )
    except (ObjectDoesNotExist, ValidationError):
        pass
    except Exception as e:
        errorLog(e)
        pass
    return False
