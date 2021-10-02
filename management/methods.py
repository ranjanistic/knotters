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
                      judgeIDs, taskSummary, taskDetail, taskSample
                      ) -> Competition:
    try:
        if not creator.is_manager:
            raise Exception(f"Unauthorized manager")

        if len(perks) < 1:
            raise Exception(f"invalid perks {perks}")
        if startAt >= endAt:
            raise Exception(f"invalid timings")
        if eachTopicMaxPoint < 0:
            raise Exception(f"invalid eachTopicMaxPoint")

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
            resultDeclared=False,
        )
        topics = Topic.objects.filter(id__in=topicIDs)
        for topic in topics:
            compete.topics.add(topic)
        judges = Profile.objects.filter(suspended=False, is_active=True, to_be_zombie=False, user__id__in=judgeIDs)
        for judge in judges:
            compete.judges.add(judge)
        perkobjs = []
        for i, perk in enumerate(perks):
            perkobjs.append(Perk(
                competition=compete,
                name=perk,
                rank=(i+1)
            ))
        Perk.objects.bulk_create(perkobjs)
        return compete
    except Exception as e:
        errorLog(e)
        return False
