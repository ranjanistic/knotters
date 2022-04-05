from compete.models import Competition, Perk
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
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
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def createCompetition(creator: Profile, title, tagline, shortdescription,
                      description, perks, startAt, endAt, eachTopicMaxPoint, topicIDs,
                      judgeIDs, taskSummary, taskDetail, taskSample, max_grouping,
                      reg_fee, fee_link, qualifier, qualifier_rank
                      ) -> Competition:
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
            raise Exception(f"invalid topics")
        for topic in topics:
            compete.topics.add(topic)
        judges = Profile.objects.filter(
            suspended=False, is_active=True, to_be_zombie=False, user__id__in=judgeIDs)
        for judge in judges:
            if judge.isBlocked(creator.user):
                continue
            compete.judges.add(judge)
        if compete.totalJudges() < 1:
            raise Exception(f"invalid judges")
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
            raise Exception("invalid perks")
        Perk.objects.bulk_create(perkobjs)
        addMethodToAsyncQueue(
            f"{APPNAME}.methods.{setupCompetitionChannel.__name__}", compete)
        return compete
    except Exception as e:
        errorLog(e)
        if compete:
            compete.delete()
        return False


def setupCompetitionChannel(compete: Competition):
    return Discord.create_channel(compete.get_nickname(), public=True, category="COMPETITIONS", message=f"Official discord channel for {compete.title} {compete.get_abs_link}")


def labelRenderData(request, type, labelID):
    """
    Individual label render data
    """
    try:
        mgm = request.user.profile.management()
        cacheKey = f"{APPNAME}_labelrenderdata_{type}_{labelID}_{mgm.id}"
        if type == Code.TOPIC:
            topic = cache.get(cacheKey, None)
            if not topic:
                topic = Topic.objects.filter(Q(id=labelID), Q(
                    Q(creator__in=[mgm.people.all()]) | Q(creator=request.user.profile))).first()
                if not topic:
                    return False
                cache.set(cacheKey, topic, settings.CACHE_MICRO)
            return dict(topic=topic)
        if type == Code.CATEGORY:
            category = cache.get(cacheKey, None)
            if not category:
                category = Category.objects.filter(Q(id=labelID), Q(
                    Q(creator__in=[mgm.people.all()]) | Q(creator=request.user.profile))).first()
                if not category:
                    return False
                cache.set(cacheKey, category, settings.CACHE_MICRO)
            return dict(category=category)
        return False
    except Exception as e:
        errorLog(e)
        return False


def competitionManagementRenderData(request, compID):
    try:
        compete = Competition.objects.get(
            id=compID, creator=request.user.profile)
        resstatus = cache.get(f"results_declaration_task_{compete.get_id}")
        certstatus = cache.get(f"certificates_allotment_task_{compete.get_id}")
        return dict(
            compete=compete,
            iscreator=(compete.creator == request.user.profile),
            declaring=(resstatus == Message.RESULT_DECLARING),
            generating=(certstatus == Message.CERTS_GENERATING)
        )
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False

from .receivers import *