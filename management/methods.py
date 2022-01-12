from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from main.methods import errorLog, renderString, renderView
from compete.models import Competition, Perk
from people.models import Topic, Profile
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)

def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def createCompetition(creator, title, tagline, shortdescription,
                      description, perks, startAt, endAt, eachTopicMaxPoint, topicIDs,
                      judgeIDs, taskSummary, taskDetail, taskSample, max_grouping,
                      reg_fee, fee_link, qualifier, qualifier_rank
                      ) -> Competition:
    compete = None
    try:
        if not creator.is_manager:
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

        taskSummary = taskSummary.replace('href=\"', 'target="_blank" href=\"/redirector?n=').replace('</script>', '!script!').replace('onclick=','').replace('()','[]')
        taskDetail = taskDetail.replace('href=\"', 'target="_blank" href=\"/redirector?n=').replace('</script>', '!script!').replace('onclick=','').replace('()','[]')
        taskSample = taskSample.replace('href=\"', 'target="_blank" href=\"/redirector?n=').replace('</script>', '!script!').replace('onclick=','').replace('()','[]')

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
        judges = Profile.objects.filter(suspended=False, is_active=True, to_be_zombie=False, user__id__in=judgeIDs)
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
        return compete
    except Exception as e:
        errorLog(e)
        if compete:
            compete.delete()
        return False

from .receivers import *