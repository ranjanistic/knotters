from django.core.handlers.wsgi import WSGIRequest
from people.models import Profile
from compete.models import Competition
from projects.models import Project
from django.db.models import Q
from django.db import models
from main.methods import renderView, classAttrsToDict, replaceUrlParamsWithStr
from main.strings import Code, url, PROJECTS, PEOPLE, COMPETE, code
from .apps import APPNAME
from .models import LocalStorage, Moderation


def renderer(request: WSGIRequest, file: str, data: dict = {}):
    data['URLS'] = {}

    def cond(key, value):
        return str(key).isupper()

    urls = classAttrsToDict(url.Moderation, cond)

    for key in urls:
        data['URLS'][key] = f"{url.getRoot(APPNAME)}{replaceUrlParamsWithStr(urls[key])}"
    return renderView(request, file, data, fromApp=APPNAME)

def getModelByType(type:str)-> models.Model:
    if type == PROJECTS: return Project
    elif type == COMPETE: return Competition
    elif type == PEOPLE: return Profile
    else: raise IllegalModerationType()

    

def getModeratorToAssignModeration(type: str, object: models.Model, ignoreModProfiles: list = [], onlyModProfiles: list = []) -> Profile:
    """
    Implementes round robin algorithm to retreive an available moderator, along with other restrictions.

    :type: The type of sub application for which the entity is to be moderated
    :object: The model object of the entity to be moderated.
    :ignoreModProfiles: The profile object list of moderators to be ignored, optionally.
    :onlyModProfiles: The profile object list of moderators to only be considered, optionally.

    In case of common object(s) between :ignoreModProfiles: and :onlyModProfiles:, ignoreModProfiles will be preferred.
    """
    try:
        current = LocalStorage.objects.get(key=Code.MODERATOR)
    except:
        current = LocalStorage.objects.create(key=Code.MODERATOR, value=0)

    ignoreModProfileIDs = []
    if type == PROJECTS:
        ignoreModProfileIDs.append(object.creator.id)
    if type == PEOPLE:
        ignoreModProfileIDs.append(object.id)

    for ignoreModProfile in ignoreModProfiles:
        ignoreModProfileIDs.append(ignoreModProfile.id)

    onlyModProfileIDs = []
    if len(onlyModProfiles) > 0:
        for onlyModProfile in onlyModProfiles:
            if not ignoreModProfileIDs.__contains__(onlyModProfile.id):
                onlyModProfileIDs.append(onlyModProfile.id)

    query = Q(~Q(id__in=ignoreModProfileIDs), id__in=onlyModProfileIDs) if len(
        onlyModProfileIDs) > 0 else ~Q(id__in=ignoreModProfileIDs)

    availableModProfiles = Profile.objects.filter(query, is_moderator=True)

    totalAvailableModProfiles = len(availableModProfiles)
    if totalAvailableModProfiles == 0:
        return False

    temp = int(current.value)
    if temp >= totalAvailableModProfiles:
        temp = 1
    else:
        temp = temp + 1
    current.value = temp
    current.save()

    return availableModProfiles[temp-1]


def requestModerationForObject(
    object: models.Model,
    type: str,
    requestData: str = '',
    referURL: str = '',
    reassignIfRejected: bool = False,
    reassignIfApproved: bool = False
) -> Moderation or bool:
    """
    Submit a subapplication entity model object for moderation.

    :object: The subapplication entity model object (Project|Profile|Competition)
    :type: The subapplication or entity type.
    :requestData: Relevent string data regarding moderation.
    :referUrl: Relevant url regarding moderation.
    :reassignIfRejected: If True, and if a moderation already exists for the :object: with status code.REJECTED, then a new moderation instance is created for it. Default False.
    :reassignIfApproved: If True, and if a moderation already exists for the :object: with status code.APPROVED, then a new moderation instance is created for it. Default False.
    """
    try:
        if type == PROJECTS:
            query = Q(type=type, project=object)
        elif type == PEOPLE:
            query = Q(type=type, profile=object)
        elif type == COMPETE:
            query = Q(type=type, competition=object)
        else:
            return False

        mod = Moderation.objects.get(query)

        if (mod.isRejected() and reassignIfRejected) or (mod.isApproved() and reassignIfApproved):
            newmoderator = getModeratorToAssignModeration(
                type=type, object=object, ignoreModProfiles=[mod.moderator])
            if not newmoderator:
                return False
            requestData = requestData if requestData else mod.request
            referURL = referURL if referURL else mod.referURL
            if type == PROJECTS:
                newmod = Moderation.objects.create(
                    type=type, project=object, moderator=newmoderator, request=requestData, referURL=referURL)
            elif type == PEOPLE:
                newmod = Moderation.objects.create(
                    type=type, profile=object, moderator=newmoderator, request=requestData, referURL=referURL)
            elif type == COMPETE:
                newmod = Moderation.objects.create(
                    type=type, competition=object, moderator=newmoderator, request=requestData, referURL=referURL)
            else:
                return False

            if newmod.type == PROJECTS:
                newmod.project.status = code.MODERATION
                newmod.project.save()
            return newmod
    except Exception as e:
        newmoderator = getModeratorToAssignModeration(type, object)
        if not newmoderator:
            return False
        if type == PROJECTS:
            newmod = Moderation.objects.create(
                project=object, type=type, moderator=newmoderator, request=requestData, referURL=referURL)
        elif type == PEOPLE:
            newmod = Moderation.objects.create(
                profile=object, type=type, moderator=newmoderator, request=requestData, referURL=referURL)
        elif type == COMPETE:
            newmod = Moderation.objects.create(
                competition=object, type=type, moderator=newmoderator, request=requestData, referURL=referURL)
        else:
            return False
        return newmod
    return False

from .receivers import *