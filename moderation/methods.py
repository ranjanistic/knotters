from django.core.handlers.wsgi import WSGIRequest
from people.models import Profile
from compete.models import Competition
from projects.models import Project
from django.db.models import Q
from django.db import models
from main.methods import renderView, errorLog
from main.strings import Code, PROJECTS, PEOPLE, COMPETE
from .apps import APPNAME
from .models import LocalStorage, Moderation


def renderer(request: WSGIRequest, file: str, data: dict = dict()):
    return renderView(request, file, data, fromApp=APPNAME)


def getModelByType(type: str) -> models.Model:
    if type == PROJECTS:
        return Project
    elif type == COMPETE:
        return Competition
    elif type == PEOPLE:
        return Profile
    else:
        raise IllegalModerationType()


def getIgnoreModProfileIDs(modType: str, object: models.Model, extraProfiles: list = list()) -> list:
    ignoreModProfileIDs = list()
    if modType == PROJECTS and isinstance(object, Project):
        ignoreModProfileIDs.append(object.creator.id)
    elif modType == PEOPLE and isinstance(object, Profile):
        ignoreModProfileIDs.append(object.id)
    elif modType == COMPETE and isinstance(object, Competition):
        if object.totalJudges() > 0:
            for judge in object.getJudges():
                ignoreModProfileIDs.append(judge.id)
        if object.totalAllParticipants() > 0:
            for participant in object.getAllParticipants():
                ignoreModProfileIDs.append(participant.id)
    else:
        return False
    for ignoreModProfile in extraProfiles:
        if not ignoreModProfileIDs.__contains__(ignoreModProfile.id):
            ignoreModProfileIDs.append(ignoreModProfile.id)
    return ignoreModProfileIDs


def getModeratorToAssignModeration(type: str, object: models.Model, ignoreModProfiles: list = list(), preferModProfiles: list = list(), onlyModProfiles: list = list()) -> Profile:
    """
    Implementes round robin algorithm to retreive an available moderator, along with other restrictions.

    :type: The type of sub application for which the entity is to be moderated
    :object: The model object of the entity to be moderated. (Profile | Project | Competition)
    :ignoreModProfiles: The profile object list of moderators to be ignored, optionally.
    :preferModProfiles: The profile object list of moderators to be considered preferably, optionally.
    :onlyModProfiles: The profile object list of moderators to only be considered, optionally.

    If :preferModProfiles: and :onlyModProfiles: are provided simultaneously, :onlyModProfiles: will only be considered.

    In case of common object(s) between :ignoreModProfiles: and :onlyModProfiles: or :preferModProfiles:, :ignoreModProfiles: will be preferred.

    """

    ignoreModProfileIDs = getIgnoreModProfileIDs(
        type, object, ignoreModProfiles)

    if ignoreModProfileIDs == False:
        raise IllegalModeration()

    defaultQuery = Q(~Q(id__in=ignoreModProfileIDs), is_moderator=True,
                     suspended=False, to_be_zombie=False, is_active=True)
    

    preferred = False
    if len(onlyModProfiles) > 0:
        onlyModProfileIDs = []
        for onlyModProfile in onlyModProfiles:
            if not ignoreModProfileIDs.__contains__(onlyModProfile.id):
                onlyModProfileIDs.append(onlyModProfile.id)
        query = Q(query, id__in=onlyModProfileIDs)
    elif len(preferModProfiles) > 0:
        preferred = True
        preferModProfileIDs = []
        for preferModProfile in preferModProfiles:
            if not ignoreModProfileIDs.__contains__(preferModProfile.id):
                preferModProfileIDs.append(preferModProfile.id)
        query = Q(query, id__in=preferModProfileIDs)

    availableModProfiles = Profile.objects.filter(query)

    totalAvailableModProfiles = len(availableModProfiles)
    if totalAvailableModProfiles == 0:
        if preferred:
            availableModProfiles = Profile.objects.filter(defaultQuery)
            totalAvailableModProfiles = len(availableModProfiles)
            if totalAvailableModProfiles == 0:
                return False
        return False

    current, _ = LocalStorage.objects.get_or_create(
        key=Code.MODERATOR, defaults={'value': 0})

    temp = int(current.value)

    if temp >= totalAvailableModProfiles:
        temp = 1
    else:
        temp += 1
    current.value = temp
    current.save()
    print(availableModProfiles)
    return availableModProfiles[temp-1]


def requestModerationForObject(
    object: models.Model,
    type: str,
    requestData: str = str(),
    referURL: str = str(),
    reassignIfRejected: bool = False,
    reassignIfApproved: bool = False
) -> Moderation or bool:
    """
    Submit a subapplication entity model object for moderation.

    :object: The subapplication entity model object (Project|Profile|Competition)
    :type: The subapplication or entity type.
    :requestData: Relevent string data regarding moderation.
    :referUrl: Relevant url regarding moderation.
    :reassignIfRejected: If True, and if a moderation already exists for the :object: with status Code.REJECTED, then a new moderation instance is created for it. Default False.
    :reassignIfApproved: If True, and if a moderation already exists for the :object: with status Code.APPROVED, then a new moderation instance is created for it. Default False.
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

        mod = Moderation.objects.filter(query).order_by('-respondOn').first()
        if not mod: raise Exception()

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
                object.status = Code.MODERATION
                object.save()
            elif type == PEOPLE:
                newmod = Moderation.objects.create(
                    type=type, profile=object, moderator=newmoderator, request=requestData, referURL=referURL)
            elif type == COMPETE:
                newmod = Moderation.objects.create(
                    type=type, competition=object, moderator=newmoderator, request=requestData, referURL=referURL)
            else:
                return False
                
            return newmod
    except Exception as e:
        newmoderator = getModeratorToAssignModeration(type, object)
        if not newmoderator:
            return False
        return assignModeratorToObject(type,object,newmoderator,requestData)
    return False

def assignModeratorToObject(type,object,moderator:Profile, requestData, referURL=''):
    try:
        if not (moderator.is_moderator and moderator.is_normal):
            raise Exception('Invalid moderator')
        if type == PROJECTS:
            newmod = Moderation.objects.create(
                project=object, type=type, moderator=moderator, request=requestData, referURL=referURL)
        elif type == PEOPLE:
            newmod = Moderation.objects.create(
                profile=object, type=type, moderator=moderator, request=requestData, referURL=referURL)
        elif type == COMPETE:
            newmod = Moderation.objects.create(
                competition=object, type=type, moderator=moderator, request=requestData, referURL=object.getLink())
        else:
            return False
        return newmod
    except Exception as e:
        errorLog(e)
        return False


from .receivers import *