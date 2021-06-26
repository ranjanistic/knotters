from people.models import Profile
from projects.models import Project
from django.db.models import Q
from .models import *
from main.methods import renderView
from .apps import APPNAME
from main.strings import PROJECTS, PEOPLE, COMPETE, code


def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


# implemented round robin algorithm
def getModerator(type: str, obj: models.Model) -> Profile:
    try:
        current = LocalStorage.objects.get(key="moderator")
    except:
        current = LocalStorage.objects.create(key="moderator", value=0)
        current.save()
    if type == PROJECTS:
        totalModerators = Profile.objects.filter(~Q(id=obj.creator.id),is_moderator=True)
    elif type == PEOPLE:
        totalModerators = Profile.objects.filter(~Q(id=obj.id),is_moderator=True)
    else: 
        totalModerators = Profile.objects.filter(is_moderator=True)
    if(totalModerators.count == 0):
        return False
    temp = int(current.value)
    if(temp >= totalModerators.count()):
        temp = 1
    else:
        temp = temp+1
    current.value = temp
    current.save()
    return totalModerators[temp-1]


def requestModeration(object: models.Model, type: str, requestData: str) -> bool:
    obj = None
    try:
        if type == PROJECTS:
            obj = Moderation.objects.get(project=object)
        elif type == PEOPLE:
            obj = Moderation.objects.get(profile=object)
        elif type == COMPETE:
            obj = Moderation.objects.get(competiton=object)

        if obj.status == code.REJECTED and obj.retries > 0:
            obj.status = code.MODERATION
            obj.moderator = getModerator()

            if type == PROJECTS:
                obj.project.status = code.MODERATION
                obj.project.save()

            obj.save()
            return True

        return False
    except:
        moderator = getModerator(type, obj)
        if not moderator:
            return False
        if type == PROJECTS:
            obj = Moderation.objects.create(
                project=object, type=type, moderator=moderator, request=requestData)
        elif type == PEOPLE:
            obj = Moderation.objects.create(
                profile=object, type=type, moderator=moderator, request=requestData)
        elif type == COMPETE:
            obj = Moderation.objects.create(
                competiton=object, type=type, moderator=moderator, request=requestData)
        obj.save()
    return True
