from compete.models import Competition
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import Q
from main.methods import errorLog, renderView
from main.strings import COMPETE, CORE_PROJECT, PEOPLE, PROJECTS, Code
from people.models import Profile
from projects.models import CoreProject, Project

from .apps import APPNAME
from .models import LocalStorage, Moderation


def renderer(request: WSGIRequest, file: str, data: dict = dict()):
    return renderView(request, file, data, fromApp=APPNAME)


def getModelByType(type: str) -> models.Model:
    if type == PROJECTS:
        return Project
    if type == CORE_PROJECT:
        return CoreProject
    elif type == COMPETE:
        return Competition
    elif type == PEOPLE:
        return Profile
    else:
        raise IllegalModerationType()


def getIgnoreModProfileIDs(modType: str, object: models.Model, extraProfiles: list = []) -> list:
    ignoreModProfileIDs = []
    if modType == PROJECTS and isinstance(object, Project):
        ignoreModProfileIDs.append(object.creator.id)
    elif modType == CORE_PROJECT and isinstance(object, CoreProject):
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
        if not (ignoreModProfile.id in ignoreModProfileIDs):
            ignoreModProfileIDs.append(ignoreModProfile.id)
    return ignoreModProfileIDs


def getObjectCreator(object: models.Model):
    if isinstance(object, Project) or isinstance(object, CoreProject):
        return object.creator
    elif isinstance(object, Competition):
        return object.creator
    elif isinstance(object, Profile):
        return object
    else:
        raise IllegalModerationType()


def getModeratorToAssignModeration(type: str, object: models.Model, ignoreModProfiles: list = [], preferModProfiles: list = [], onlyModProfiles=False, samplesize=100, internal=False) -> Profile:
    """
    Implementes round robin algorithm to retreive an available moderator, along with other restrictions.

    :type: The type of sub application for which the entity is to be moderated
    :object: The instance of the entity to be moderated. (Profile | Project | Coreproject | Competition)
    :ignoreModProfiles: The profile object list of moderators to be ignored, optionally.
    :preferModProfiles: The profile object list of moderators to be considered preferable, optionally.
    :onlyModProfiles: The profile object list of moderators to only be considered, optionally. Suitable for organizations.
    :samplesize: The number of moderators in a set to be considered.
    :internal: If the moderation is internal or not (useful for managements).
    If :preferModProfiles: and :onlyModProfiles: are provided simultaneously, :onlyModProfiles: will only be considered.

    In case of common object(s) between :ignoreModProfiles: and :onlyModProfiles: or :preferModProfiles:, :ignoreModProfiles: will be the deciding factor.

    """

    ignoreModProfileIDs = getIgnoreModProfileIDs(
        type, object, ignoreModProfiles)

    if ignoreModProfileIDs == False:
        raise IllegalModeration()

    defaultQuery = Q(is_moderator=True,
                     suspended=False, to_be_zombie=False, is_active=True)

    query = defaultQuery

    preferred = False
    creator = getObjectCreator(object)

    if onlyModProfiles:
        if len(onlyModProfiles) > 0:
            onlyModProfileIDs = []
            for onlyModProfile in onlyModProfiles:
                if not (onlyModProfile.id in ignoreModProfileIDs):
                    onlyModProfileIDs.append(onlyModProfile.id)
            if len(onlyModProfileIDs) > 0:
                query = Q(query, id__in=onlyModProfileIDs)
            if len(onlyModProfileIDs) == 1 and creator.is_manager():
                mprof = list(
                    filter(lambda m: m.id == onlyModProfileIDs[0], list(onlyModProfiles)))[0]
                if mprof.isBlockedProfile(creator):
                    return False
                return mprof
    elif len(preferModProfiles) > 0:
        preferred = True
        preferModProfileIDs = []
        for preferModProfile in preferModProfiles:
            if not (preferModProfile.id in ignoreModProfileIDs):
                preferModProfileIDs.append(preferModProfile.id)
        if len(preferModProfileIDs) > 0:
            query = Q(query, id__in=preferModProfileIDs)

    availableModProfiles = Profile.objects.exclude(
        id__in=ignoreModProfileIDs).filter(query).distinct()[:samplesize]

    totalAvailableModProfiles = len(availableModProfiles)
    if totalAvailableModProfiles == 0:
        if preferred:
            availableModProfiles = Profile.objects.exclude(
                id__in=ignoreModProfileIDs).filter(defaultQuery).distinct()[:samplesize]
            totalAvailableModProfiles = len(availableModProfiles)
            if totalAvailableModProfiles == 0:
                return False
        return False

    finalAvailableModProfiles = availableModProfiles

    for modprof in availableModProfiles:
        if modprof.isBlockedProfile(creator):
            finalAvailableModProfiles.remove(modprof)

    finalAvailableModProfiles = sorted(
        finalAvailableModProfiles, key=lambda m: m.xp, reverse=True)
    totalAvailableModProfiles = len(finalAvailableModProfiles)

    if totalAvailableModProfiles == 0:
        errorLog(f"no mods available {object.id}")
        return False

    robinIndexkey = Code.MODERATOR
    lastModeratorkey = Code.LAST_MODERATOR

    if internal and creator.is_manager():
        robinIndexkey = f"moderator_rr_{creator.manager_id}"
        lastModeratorkey = f"{lastModeratorkey}_{creator.manager_id}"

    robinIndexValue = cache.get(robinIndexkey, None)

    if robinIndexValue == None:
        robinStore, _ = LocalStorage.objects.get_or_create(
            key=robinIndexkey, defaults=dict(value=0))

        robinIndexValue = int(robinStore.value)

        if robinIndexValue >= totalAvailableModProfiles:
            robinIndexValue = 1
        else:
            robinIndexValue += 1

        robinStore.value = robinIndexValue
        robinStore.save()
        cache.set(robinIndexkey, robinIndexValue)
    else:
        if robinIndexValue >= totalAvailableModProfiles:
            robinIndexValue = 1
        else:
            robinIndexValue += 1

        done = LocalStorage.objects.filter(
            key=robinIndexkey).update(value=robinIndexValue)
        if done == 0:
            LocalStorage.objects.create(
                key=robinIndexkey, value=robinIndexValue)
        cache.set(robinIndexkey, robinIndexValue)

    newlastmoderator = finalAvailableModProfiles[robinIndexValue-1]
    if totalAvailableModProfiles > 1:
        lastModeratorID = cache.get(lastModeratorkey, None)
        created = False
        if lastModeratorID == None:
            lastModeratorStore, created = LocalStorage.objects.get_or_create(
                key=lastModeratorkey, defaults=dict(value=finalAvailableModProfiles[robinIndexValue-1].id))
            lastModeratorID = lastModeratorStore.value
            cache.set(lastModeratorkey, lastModeratorID)
        if not created:
            filtererd = list(filter(lambda m: str(m.id) == str(
                lastModeratorID), list(finalAvailableModProfiles)))
            if len(filtererd) and robinIndexValue > 1:
                finalAvailableModProfiles.remove(filtererd[0])
                finalAvailableModProfiles.insert(0, filtererd[0])
            newlastmoderator = finalAvailableModProfiles[robinIndexValue-1]
            done = LocalStorage.objects.filter(
                key=lastModeratorkey).update(value=newlastmoderator.id)
            if done == 0:
                LocalStorage.objects.create(
                    key=lastModeratorkey, value=newlastmoderator.id)
            cache.set(lastModeratorkey, newlastmoderator.id)
    return newlastmoderator


def requestModerationForObject(
    object: models.Model,
    type: str,
    requestData: str = str(),
    referURL: str = str(),
    reassignIfRejected: bool = False,
    reassignIfApproved: bool = False,
    useInternalMods=False,
    stale_days=3,
    chosenModerator: Profile = None
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

        mod = Moderation.objects.filter(query).order_by(
            '-requestOn', '-respondOn').first()

        preferModProfiles = None
        onlyModProfiles = None

        useInternalMods = useInternalMods and object.creator.is_manager()
        if chosenModerator:
            if chosenModerator.is_moderator and chosenModerator.is_normal:
                onlyModProfiles = [chosenModerator]
            else:
                raise Exception("Chosen moderator", chosenModerator,
                                "is not available for ", object)
        elif useInternalMods:
            onlyModProfiles = object.creator.management().moderators()
            if not len(onlyModProfiles):
                return False
        else:
            if type == PROJECTS:
                preferModProfiles = Profile.objects.filter(
                    is_moderator=True, suspended=False, is_active=True, to_be_zombie=False, topics__in=object.category.topics).distinct()

        if not mod:
            if not preferModProfiles:
                preferModProfiles = []

            newmoderator = getModeratorToAssignModeration(
                type, object, preferModProfiles=preferModProfiles, onlyModProfiles=onlyModProfiles, internal=useInternalMods)

            if not newmoderator:
                return False
            return assignModeratorToObject(type, object, newmoderator, requestData, stale_days=stale_days, internal_mod=useInternalMods)

        if (mod.isRejected() and reassignIfRejected) or (mod.isApproved() and reassignIfApproved) or mod.is_stale:
            if preferModProfiles:
                preferModProfiles.exclude(id=mod.moderator.id)
            else:
                preferModProfiles = []
            if onlyModProfiles:
                onlyModProfiles.exclude(id=mod.moderator.id)

            newmoderator = getModeratorToAssignModeration(
                type=type, object=object, ignoreModProfiles=[mod.moderator], preferModProfiles=preferModProfiles, onlyModProfiles=onlyModProfiles, internal=useInternalMods)
            if not newmoderator:
                return False

            requestData = requestData if requestData else mod.request
            referURL = referURL if referURL else mod.referURL

            newmod = assignModeratorToObject(
                type, object, newmoderator, requestData, referURL, stale_days=stale_days, internal_mod=useInternalMods)

            if not newmod:
                return False

            if type == PROJECTS:
                object.status = Code.MODERATION
                object.save()

            if mod.is_stale:
                mod.delete()
            return newmod
    except Exception as e:
        errorLog(e)
        return False


def requestModerationForCoreProject(
    coreproject: CoreProject,
    requestData: str = str(),
    referURL: str = str(),
    reassignIfRejected: bool = False,
    reassignIfApproved: bool = False,
    useInternalMods=False,
    stale_days=3,
    chosenModerator: Profile = None,
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

        query = Q(type=type, coreproject=coreproject)
        mod = Moderation.objects.filter(query).order_by(
            '-requestOn', '-respondOn').first()
        preferModProfiles = None
        onlyModProfiles = None

        if chosenModerator:
            if chosenModerator.is_moderator and chosenModerator.is_normal and not chosenModerator.isBlockedProfile(coreproject.creator):
                onlyModProfiles = [chosenModerator]
            else:
                raise Exception("Chosen moderator", chosenModerator,
                                "is not available for ", coreproject)
        elif useInternalMods and coreproject.creator.is_manager():
            onlyModProfiles = coreproject.creator.management().moderators()
            if not len(onlyModProfiles):
                return False
        else:
            preferModProfiles = Profile.objects.filter(
                is_moderator=True, suspended=False, is_active=True, to_be_zombie=False, topics__in=coreproject.category.topics).distinct()

        if not mod:
            if not preferModProfiles:
                preferModProfiles = []
            newmoderator = getModeratorToAssignModeration(
                type=CORE_PROJECT, object=coreproject, preferModProfiles=preferModProfiles, onlyModProfiles=onlyModProfiles, internal=useInternalMods)
            if not newmoderator:
                raise Exception("No moderator available for ", coreproject)
            return assignModeratorToCoreProject(coreproject, newmoderator, requestData, stale_days=stale_days, internal_mod=useInternalMods)

        if (mod.isRejected() and reassignIfRejected) or (mod.isApproved() and reassignIfApproved) or mod.is_stale:
            if preferModProfiles:
                preferModProfiles.exclude(id=mod.moderator.id)
            else:
                preferModProfiles = []
            if onlyModProfiles:
                onlyModProfiles.exclude(id=mod.moderator.id)

            newmoderator = getModeratorToAssignModeration(type=CORE_PROJECT, object=coreproject, ignoreModProfiles=[
                                                          mod.moderator], preferModProfiles=preferModProfiles, onlyModProfiles=onlyModProfiles, internal=useInternalMods)
            if not newmoderator:
                raise Exception("No moderator available for ", coreproject)

            requestData = requestData if requestData else mod.request
            referURL = referURL if referURL else mod.referURL
            newmod = assignModeratorToCoreProject(
                coreproject, newmoderator, requestData, referURL, stale_days=stale_days, internal_mod=useInternalMods)
            if not newmod:
                raise Exception("Moderator not assigned ",
                                coreproject, newmoderator)
            else:
                coreproject.status = Code.MODERATION
                coreproject.save()
            if mod.is_stale:
                mod.delete()
            return newmod
    except Exception as e:
        errorLog(e)
        return False


def assignModeratorToObject(type, object, moderator: Profile, requestData='', referURL='', stale_days=3, internal_mod=False):
    try:
        if not (moderator.is_moderator and moderator.is_normal):
            raise Exception('Invalid moderator')
        if type == PROJECTS:
            newmod = Moderation.objects.create(
                project=object, type=type, moderator=moderator, request=requestData, referURL=referURL, stale_days=stale_days, internal_mod=internal_mod)
        elif type == PEOPLE:
            newmod = Moderation.objects.create(
                profile=object, type=type, moderator=moderator, request=requestData, referURL=referURL, stale_days=stale_days, internal_mod=internal_mod)
        elif type == COMPETE:
            newmod = Moderation.objects.create(
                competition=object, type=type, moderator=moderator, request=requestData, referURL=object.getLink(), stale_days=stale_days, internal_mod=internal_mod)
        else:
            return False
        return newmod
    except Exception as e:
        errorLog(e)
        return False


def assignModeratorToCoreProject(coreproject: CoreProject, moderator: Profile, requestData='', referURL='', stale_days=3, internal_mod=False):
    try:
        if not (moderator.is_moderator and moderator.is_normal):
            raise Exception('Invalid moderator', moderator)
        return Moderation.objects.create(coreproject=coreproject, type=CORE_PROJECT, moderator=moderator, request=requestData, referURL=referURL, stale_days=stale_days, internal_mod=internal_mod)
    except Exception as e:
        errorLog(e)
        return False


def moderationRenderData(request, modID):
    try:
        moderation = Moderation.objects.get(id=modID)
        isModerator = moderation.moderator == request.user.profile
        isRequestor = moderation.isRequestor(request.user.profile)
        if not isRequestor and not isModerator:
            return False
        data = dict(moderation=moderation, ismoderator=isModerator)
        if moderation.type == COMPETE:
            if isRequestor:
                data = dict(
                    **data, allSubmissionsMarkedByJudge=moderation.competition.allSubmissionsMarkedByJudge(request.user.profile))
        if moderation.type == PROJECTS and (moderation.resolved or moderation.is_stale):
            forwarded = None
            forwardeds = Moderation.objects.filter(
                type=PROJECTS, project=moderation.project, resolved=False).order_by('-requestOn', '-respondOn')
            if len(forwardeds) and forwardeds[0].moderator != moderation.moderator:
                forwarded = forwardeds[0]
            data = dict(**data, forwarded=forwarded)
        elif moderation.type == CORE_PROJECT and (moderation.resolved or moderation.is_stale):
            forwarded = None
            forwardeds = Moderation.objects.filter(
                type=CORE_PROJECT, coreproject=moderation.coreproject, resolved=False).order_by('-requestOn', '-respondOn')
            if len(forwardeds) and forwardeds[0].moderator != moderation.moderator:
                forwarded = forwardeds[0]
            data = dict(**data, forwarded=forwarded)
        return data
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False

from .receivers import *