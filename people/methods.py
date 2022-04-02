from requests import get as getRequest
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http.response import HttpResponse
from allauth.socialaccount.models import SocialAccount, SocialToken
from django.core.cache import cache
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.discord.provider import DiscordProvider
from allauth.socialaccount.providers.linkedin_oauth2.provider import LinkedInOAuth2Provider
from django.conf import settings
from main.methods import errorLog, renderString, renderView
from main.strings import Code, profile as profileString, COMPETE
from projects.models import BaseProject, Project
from moderation.models import Moderation
from compete.models import Competition, CompetitionJudge, Result
from .models import ProfileSetting, Topic, User, Profile, isPictureDeletable
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def convertToFLname(string: str) -> str and str:
    """
    Converts the given string to first and last name format.

    :string: Assuming a full name in this parameter, segragation of name parts will take place.
    :returns: firtsname, lastname
    """
    name = str(string)
    namesequence = name.split(" ")
    firstname = namesequence[0]
    del namesequence[0]
    if len(namesequence) > 0:
        lastname = " ".join(namesequence)
    else:
        lastname = str()
    fullname = f"{firstname} {lastname}"
    if len(fullname) > 70:
        fullname = fullname[:(70-len(fullname))]
        return convertToFLname(fullname)
    return firstname, lastname


def filterBio(string: str) -> str:
    """
    Trims given string (assuming to be profile bio) to a certain length limit.

    :string: Assuming this to be user profile bio, operations will take place.
    """
    bio = str(string)
    if len(bio) > 300:
        bio = bio[:(300-len(bio))]
        return filterBio(bio)
    return bio


def addTopicToDatabase(topic: str, creator=None) -> Topic:
    topic = str(topic).strip().replace('\n', str())
    if not topic:
        return False
    topicObj = None
    try:
        topicObj = Topic.objects.filter(name__iexact=topic).first()
        if not topicObj:
            topicObj = Topic.objects.create(name=topic, creator=creator)
    except:
        if not topicObj:
            topicObj = Topic.objects.create(name=topic, creator=creator)
    return topicObj


PROFILE_SECTIONS = [profileString.OVERVIEW, profileString.PROJECTS, profileString.FRAMEWORKS,
                    profileString.CONTRIBUTION, profileString.ACTIVITY, profileString.MODERATION,
                    profileString.ACHEIVEMENTS, profileString.COMPETITIONS, profileString.MENTORSHIP, profileString.PEOPLE]

SETTING_SECTIONS = [profileString.setting.ACCOUNT,
                    profileString.setting.PREFERENCE, profileString.setting.SECURITY]


def profileRenderData(request, userID=None, nickname=None):
    try:
        cacheKey = f"{APPNAME}_profiledata"
        if userID:
            cacheKey = f"{cacheKey}_{userID}"
            profile = cache.get(cacheKey, None)
            if not profile:
                profile = Profile.objects.get(
                    user__id=userID, to_be_zombie=False, is_active=True)
                cache.set(cacheKey, profile, settings.CACHE_INSTANT)
        else:
            cacheKey = f"{cacheKey}_{nickname}"
            profile = cache.get(cacheKey, None)
            if not profile:
                profile = Profile.objects.get(
                    nickname=nickname, to_be_zombie=False, is_active=True)
                cache.set(cacheKey, profile, settings.CACHE_INSTANT)

        authenticated = request.user.is_authenticated
        self = authenticated and request.user.profile == profile
        is_admirer = False
        if not self:
            if profile.suspended:
                return False
            if authenticated:
                if profile.isBlocked(request.user):
                    return False
                is_admirer = profile.admirers.filter(
                    user=request.user).exists()

        gh_orgID = None
        has_ghID = profile.has_ghID()
        if has_ghID:
            gh_orgID = profile.gh_orgID()
        is_manager = profile.is_manager()

        return dict(
            person=profile.user, self=self, has_ghID=has_ghID, gh_orgID=gh_orgID, is_manager=is_manager, is_admirer=is_admirer
        )
    except ObjectDoesNotExist:
        return False
    except Exception as e:
        errorLog(e)
        return False


def getProfileSectionData(section: str, profile: Profile, requestUser: User) -> dict:

    if requestUser.is_authenticated and profile.isBlocked(requestUser) or not profile.is_active:
        return None
    cachekey = f"{section}_{profile.user.id}"
    try:
        selfprofile = requestUser == profile.user
        data = dict(
            self=selfprofile,
            person=profile.user
        )
        if not selfprofile:
            cachekey = f"{cachekey}_{requestUser.id}"
        if section == profileString.OVERVIEW:
            pass
        elif section == profileString.PROJECTS:
            projects = cache.get(cachekey, [])
            if not len(projects):
                projects = BaseProject.objects.filter(Q(Q(trashed=False), Q(creator=profile)|Q(co_creators=profile))).order_by("-createdOn").distinct()

            if not selfprofile:
                projects = projects.filter(suspended=False)
                data[Code.APPROVED] = list(
                    filter(lambda p: p.is_approved, projects))
            else:
                data[Code.APPROVED] = list(
                    filter(lambda p: p.is_approved, projects))
                data[Code.MODERATION] = list(
                    filter(lambda p: p.is_pending, projects))
                data[Code.REJECTED] = list(
                    filter(lambda p: p.is_rejected, projects))
            if len(projects):
                cache.set(cachekey, projects, settings.CACHE_INSTANT)
        elif section == profileString.ACHEIVEMENTS:
            results = cache.get(f"{cachekey}{Code.RESULTS}", [])
            if not len(results):
                results = Result.objects.filter(
                    submission__members=profile).order_by('-rank', '-points')
                if len(results):
                    cache.set(cachekey, results, settings.CACHE_INSTANT)
            judements = cache.get(f"{cachekey}{Code.JUDGEMENTS}", [])
            if not len(judements):
                judements = CompetitionJudge.objects.filter(
                    competition__resultDeclared=True, judge=profile).order_by("-competition__createdOn")
                if len(judements):
                    cache.set(cachekey, judements, settings.CACHE_INSTANT)
            moderations = cache.get(f"{cachekey}{Code.MODERATIONS}", [])
            if not len(moderations):
                moderations = Moderation.objects.filter(
                    type=COMPETE, moderator=profile, resolved=True, status=Code.APPROVED, competition__resultDeclared=True).order_by('-respondOn')
                if len(moderations):
                    cache.set(cachekey, moderations, settings.CACHE_INSTANT)
            data[Code.RESULTS] = results
            data[Code.JUDGEMENTS] = judements
            data[Code.MODERATIONS] = moderations
        elif section == profileString.FRAMEWORKS:
            frameworks = cache.get(cachekey, [])
            if not len(frameworks):
                if selfprofile:
                    frameworks = Framework.objects.filter(
                        creator=profile, trashed=False).order_by("-createdOn")
                else:
                    frameworks = Framework.objects.filter(
                        creator=profile, trashed=False, is_draft=False).order_by("-createdOn")
                if len(frameworks):
                    cache.set(cachekey, frameworks, settings.CACHE_INSTANT)
            data[Code.FRAMEWORKS] = frameworks
        elif section == profileString.CONTRIBUTION:
            pass
        elif section == profileString.ACTIVITY:
            pass
        elif section == profileString.MODERATION:
            if profile.is_moderator:
                mods = []
                if not selfprofile:
                    mods = cache.get(cachekey, [])
                if not len(mods):
                    mods = Moderation.objects.filter(moderator=profile)
                    if len(mods) and not selfprofile:
                        cache.set(cachekey, mods, settings.CACHE_INSTANT)
                data[Code.UNRESOLVED] = list(filter(lambda m: not m.is_stale or m.competition, list(
                    mods.filter(resolved=False).order_by('-requestOn'))))
                data[Code.APPROVED] = mods.filter(
                    resolved=True, status=Code.APPROVED).order_by('-respondOn')
                data[Code.REJECTED] = mods.filter(
                    resolved=True, status=Code.REJECTED).order_by('-respondOn')
        elif section == profileString.COMPETITIONS:
            if profile.is_manager():
                data[Code.COMPETITIONS] = Competition.objects.filter(
                    creator=profile).order_by("-createdOn")
        elif section == profileString.PEOPLE:
            mgm = profile.management()
            if mgm:
                data[Code.PEOPLE] = mgm.people.filter(
                    is_active=True, suspended=False, to_be_zombie=False).order_by("user__first_name")
        elif section == profileString.MENTORSHIP:
            if profile.is_mentor:
                data[Code.MENTORSHIPS] = Project.objects.filter(mentor=profile)
        else:
            return False
        return data
    except Exception as e:
        errorLog(e)
        return False


def getProfileSectionHTML(profile: Profile, section: str, request: WSGIRequest) -> str:
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = dict()
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, profile, request.user)
            break
    return rendererstr(request, f"profile/{section}", data)


def getSettingSectionData(section: str, user: User, requestuser: User) -> dict:
    data = dict()
    if not requestuser.is_authenticated:
        return data
    if section == profileString.Setting.ACCOUNT:
        pass
    if section == profileString.Setting.PREFERENCE:
        try:
            data[Code.SETTING] = ProfileSetting.objects.get(
                profile=user.profile)
        except:
            pass
    if section == profileString.Setting.SECURITY:
        pass
    return data


def getSettingSectionHTML(user: User, section: str, request: WSGIRequest) -> str:
    if not SETTING_SECTIONS.__contains__(section) or request.user != user:
        return False
    data = dict()
    for sec in SETTING_SECTIONS:
        if sec == section:
            data = getSettingSectionData(sec, user, request.user)
            break
    return rendererstr(request, f"setting/{section}", data)


def getProfileImageBySocialAccount(socialaccount: SocialAccount) -> str:
    """
    Returns user profile image url by social account.
    """
    try:
        if socialaccount.provider == GitHubProvider.id:
            avatar = socialaccount.get_avatar_url()
        if socialaccount.provider == GoogleProvider.id:
            link = socialaccount.get_avatar_url()
            linkpart = link.split("=")[0]
            sizesplit = link.split("=")[1].split("-")
            sizesplit.remove(sizesplit[0])
            avatar = "=".join(
                [linkpart, "-".join(["s512", "-".join(sizesplit)])])
        if socialaccount.provider == DiscordProvider.id:
            avatar = f"{socialaccount.get_avatar_url()}?size=1024"
        if socialaccount.provider == LinkedInOAuth2Provider.id:
            avatar = socialaccount.get_avatar_url()
            if not avatar:
                access_token = SocialToken.objects.get(
                    account=socialaccount, account__provider=LinkedInOAuth2Provider.id)
                r = getRequest(f"https://api.linkedin.com/v2/me?projection=(profilePicture("
                               f"displayImage~:playableStreams))&oauth2_access_token={access_token}")
                profile_pic_json = r.json().get('profilePicture')
                elements = profile_pic_json['displayImage~']['elements']
                avatar = elements[len(elements) -
                                  1]['identifiers'][0]['identifier']
        if avatar:
            return avatar
        return defaultImagePath()
    except:
        return defaultImagePath()


def isPictureSocialImage(picture: str) -> str:
    """
    If the given url points to a oauth provider account profile image, returns the provider id.
    """
    if isPictureDeletable(picture):
        return False

    providerID = None
    for id in [DiscordProvider.id, GitHubProvider.id, GoogleProvider.id, LinkedInOAuth2Provider.id, "licdn.com"]:
        if str(picture).__contains__(id):
            providerID = id
            break
    return providerID


def getUsernameFromGHSocial(ghSocial: SocialAccount) -> str or None:
    """
    Extracts github ID of user from their github profile url.
    """
    try:
        url = ghSocial.get_profile_url()
        urlparts = str(url).split('/')
        return urlparts[len(urlparts)-1] if urlparts[len(urlparts)-1] else None
    except:
        return None

from .receivers import *