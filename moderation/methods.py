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
def getModerator(type: str, object: models.Model, ignoreModProfile: Profile = None) -> Profile:
    """
    :type: The type of sub application for which the entity is to be moderated
    :object: The model object of the entity to be moderated.
    :ignoreMod: The profile object of moderator to be ignored, optionally.
    """
    try:
        current = LocalStorage.objects.get(key="moderator")
    except:
        current = LocalStorage.objects.create(key="moderator", value=0)
        current.save()
    if type == PROJECTS:
        totalModProfiles = Profile.objects.filter(
            ~Q(id=object.creator.id), is_moderator=True)
    elif type == PEOPLE:
        totalModProfiles = Profile.objects.filter(
            ~Q(id=object.id), is_moderator=True)
    else:
        totalModProfiles = Profile.objects.filter(is_moderator=True)
    if(totalModProfiles.count == 0):
        return False
    if ignoreModProfile:
        totalModProfiles = totalModProfiles.exclude(id=ignoreModProfile.id)
    temp = int(current.value)
    if(temp >= totalModProfiles.count()):
        temp = 1
    else:
        temp = temp+1
    current.value = temp
    current.save()
    return totalModProfiles[temp-1]


def requestModeration(object: models.Model, type: str, requestData: str = '', referURL: str = '') -> bool:
    """
    Submit a subapplication entity model object for moderation. If moderation already exists and retryable,
    then assignes a new moderator to existing moderation of object.

    :object: The subapplication entity model object (Project|Profile|Competition)
    :type: The subapplication or entity type.
    :requestData: Any relevent data regarding moderation
    :referUrl: Any relevant url regarding moderation.

    """
    mod = None
    try:
        if type == PROJECTS:
            mod = Moderation.objects.get(project=object)
        elif type == PEOPLE:
            mod = Moderation.objects.get(profile=object)
        elif type == COMPETE:
            mod = Moderation.objects.get(competiton=object)
        else:
            return False

        if mod.isRejected() and mod.canRetry():
            mod.status = code.MODERATION
            mod.moderator = getModerator(
                type=type, object=object, ignoreModProfile=mod.moderator)
            mod.response = ''
            if mod.type == PROJECTS:
                mod.project.status = code.MODERATION
                mod.project.save()

            mod.save()
            return True

        return False
    except:
        moderator = getModerator(type, object)
        if not moderator:
            return False
        if type == PROJECTS:
            mod = Moderation.objects.create(
                project=object, type=type, moderator=moderator, request=requestData, referURL=referURL)
        elif type == PEOPLE:
            mod = Moderation.objects.create(
                profile=object, type=type, moderator=moderator, request=requestData, referURL=referURL)
        elif type == COMPETE:
            mod = Moderation.objects.create(
                competiton=object, type=type, moderator=moderator, request=requestData, referURL=referURL)
        mod.save()
    return True
