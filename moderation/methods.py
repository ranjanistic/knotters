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
def getModerator(type: str, object: models.Model) -> Profile:
    """
    :type: The type of sub application for which the entity is to be moderated
    :object: The model object of the entity to be moderated.
    """
    try:
        current = LocalStorage.objects.get(key="moderator")
    except:
        current = LocalStorage.objects.create(key="moderator", value=0)
        current.save()
    if type == PROJECTS:
        totalModerators = Profile.objects.filter(~Q(id=object.creator.id),is_moderator=True)
    elif type == PEOPLE:
        totalModerators = Profile.objects.filter(~Q(id=object.id),is_moderator=True)
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


def requestModeration(object: models.Model, type: str, requestData: str, referURL:str='') -> bool:
    """
    Submit a subapplication entity model object for moderation.

    :object: The subapplication entity model object
    :type: The subapplication or entity type.
    :requestData: Any relevent data regarding moderation
    :referUrl: Any relevant url regarding moderation.

    """
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
        moderator = getModerator(type, object)
        if not moderator:
            return False
        if type == PROJECTS:
            obj = Moderation.objects.create(
                project=object, type=type, moderator=moderator, request=requestData, referURL=referURL)
        elif type == PEOPLE:
            obj = Moderation.objects.create(
                profile=object, type=type, moderator=moderator, request=requestData,referURL=referURL)
        elif type == COMPETE:
            obj = Moderation.objects.create(
                competiton=object, type=type, moderator=moderator, request=requestData,referURL=referURL)
        obj.save()
    return True
