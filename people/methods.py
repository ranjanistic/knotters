from re import sub as re_sub
from uuid import UUID

from allauth.socialaccount.models import SocialAccount, SocialToken
from allauth.socialaccount.providers.discord.provider import DiscordProvider
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.linkedin_oauth2.provider import \
    LinkedInOAuth2Provider
from compete.models import Competition, CompetitionJudge, Result
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http.response import HttpResponse
from main.methods import errorLog, renderString, renderView, addMethodToAsyncQueue
from main.strings import COMPETE, Code, Browse
from main.strings import profile as profileString
from moderation.models import Moderation
from projects.models import BaseProject, Project
from requests import get as getRequest
from howto.models import Article
from .apps import APPNAME
from .models import (Framework, Profile, ProfileSetting, Topic, User,
                     defaultImagePath, isPictureDeletable)


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Renders the given file with the given data under templates/people

    Args:
        request (WSGIRequest): The request object.
        file (str): The file to render under templates/people, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        HttpResponse: The rendered text/html view with default and provided context.
    """
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Returns text/html content as http response with the given data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file for html content under templates/people, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        HttpResponse: The text/html string content http response with default and provided context.
    """
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def convertToFLname(string: str) -> str:
    """Converts the given string to first and last name format.

    Args:
        string (str): The string to convert.

    Returns:
        str, str: firstname, lastname.

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
        fullname = fullname[:70]
        return convertToFLname(fullname)
    return firstname, lastname


def filterBio(string: str) -> str:
    """Trims given string (assuming to be profile bio) to a certain length limit.

    Args:
        string (str): Assuming this to be user profile bio, operations will take place.

    Returns:
        str: Filtered string based profile bio.
    """
    bio = str(string)
    if len(bio) > 300:
        bio = bio[:(300-len(bio))]
        return filterBio(bio)
    return bio

def filterExtendedBio(string: str) -> str:
    """Trims given string (assuming to be profile extended bio) to a certain length limit.

    Args:
        string (str): Assuming this to be user profile extended bio, operations will take place.

    Returns:
        str: Filtered string based profile extended bio.
    """
    extended_bio=str(string)
    if len(extended_bio) > 500:
        extended_bio=extended_bio[:(500-len(extended_bio))]
        return filterExtendedBio(extended_bio)
    return extended_bio


def addTopicToDatabase(topic: str, creator: Profile = None, tags: list = []) -> Topic:
    """Adds a new topic to the database.

    Args:
        topic (str): The topic name to add.
        creator (Profile, optional): The profile who created the topic. Defaults to knottersbot.
        tags (list<Tag>, optional): tags to associate with the topic. Defaults to [].

    Returns:
        Topic: The newly created topic instance.
    """
    topic = re_sub(r'[^a-zA-Z0-9\/\- ]', "", topic[:50])
    topic = " ".join(list(filter(lambda t: t, topic.split(' '))))
    topic = "-".join(list(filter(lambda t: t, topic.split('-'))))
    topic = "/".join(list(filter(lambda t: t, topic.split('/')))).capitalize()
    if not topic:
        return False
    topicObj = None
    if not creator:
        creator = Profile.KNOTBOT()
    try:
        topicObj: Topic = Topic.objects.filter(name__iexact=topic).first()
        if not topicObj:
            topicObj: Topic = Topic.objects.create(name=topic, creator=creator)
    except:
        if not topicObj:
            topicObj: Topic = Topic.objects.create(name=topic, creator=creator)
    if len(tags):
        topicObj.tags.set(tags)
    return topicObj


PROFILE_SECTIONS = [profileString.OVERVIEW, profileString.PROJECTS, profileString.FRAMEWORKS, profileString.ARTICLES, 
                    profileString.CONTRIBUTION, profileString.ACTIVITY, profileString.MODERATION,
                    profileString.ACHEIVEMENTS, profileString.COMPETITIONS, profileString.MENTORSHIP, profileString.PEOPLE]

SETTING_SECTIONS = [profileString.setting.ACCOUNT,
                    profileString.setting.PREFERENCE, profileString.setting.SECURITY]


def profileRenderData(request: WSGIRequest, userID: UUID = None, nickname: str = None) -> dict:
    """Returns the context data to render a profile page.

    Args:
        request (WSGIRequest): The request object.
        userID (UUID, optional): The user's id. Defaults to None.
        nickname (str, optional): The user's nickname. Defaults to None.

    NOTE: Only one of the userID or nickname are allowed to be None. If nickname is provided, it will be preferred.

    Returns:
        dict: The context data to render a profile page.
    """
    try:
        
        profile: Profile = Profile.get_cache_one(nickname=nickname, userID=userID, throw=False, is_active=True)
        if not profile:
            profile: Profile = Profile.get_cache_one(nickname=nickname, userID=userID, throw=False, is_active=False)
        authenticated = request.user.is_authenticated
        self: bool = authenticated and request.user.profile == profile
        is_admirer = False
        
        if not self:
            if profile.suspended:
                return False
            if not profile.is_active:
                return False
            if authenticated:
                if profile.isBlocked(request.user):
                    return False
                is_admirer: bool = profile.admirers.filter(
                    user=request.user).exists()

        gh_orgID = None
        has_ghID = profile.has_ghID()
        if has_ghID:
            gh_orgID = profile.gh_orgID()
        is_manager = profile.is_manager()
        return dict(
            person=profile.user,
            self=self,
            has_ghID=has_ghID,
            gh_orgID=gh_orgID,
            is_manager=is_manager,
            is_admirer=is_admirer
        )
    except (ObjectDoesNotExist, ValidationError):
        return False
    except Exception as e:
        errorLog(e)
        return False


def getProfileSectionData(section: str, profile: Profile, requestUser: User) -> dict:
    """Returns the context data to render a profile section.

    Args:
        section (str): The section to render.
        profile (Profile): The profile to render.
        requestUser (User): The requesting user.

    Returns:
        dict: The context data to render a profile section.
    """
    if requestUser.is_authenticated and profile.isBlocked(requestUser) or not profile.is_active:
        raise ObjectDoesNotExist(profile, requestUser)
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
                projects = BaseProject.objects.filter(Q(Q(trashed=False), Q(
                    creator=profile) | Q(co_creators=profile))).order_by("-createdOn").distinct()

            if not selfprofile:
                projects = projects.filter(suspended=False)
                data[Code.APPROVED] = list(
                    filter(lambda p: p.is_approved(), projects))
            else:
                data[Code.APPROVED] = list(
                    filter(lambda p: p.is_approved(), projects))
                data[Code.MODERATION] = list(
                    filter(lambda p: p.is_pending(), projects))
                data[Code.REJECTED] = list(
                    filter(lambda p: p.is_rejected(), projects))
            if len(projects):
                cache.set(cachekey, projects, settings.CACHE_INSTANT)
        elif section == profileString.ACHEIVEMENTS:
            results = cache.get(f"{cachekey}{Code.RESULTS}", [])
            if not len(results):
                results = Result.objects.filter(
                    submission__members=profile).order_by('-rank', '-points')
                cache.set(cachekey, results, settings.CACHE_INSTANT)
            judements = cache.get(f"{cachekey}{Code.JUDGEMENTS}", [])
            if not len(judements):
                judements = CompetitionJudge.objects.filter(
                    competition__resultDeclared=True, judge=profile).order_by("-competition__createdOn")
                cache.set(cachekey, judements, settings.CACHE_INSTANT)
            moderations = cache.get(f"{cachekey}{Code.MODERATIONS}", [])
            if not len(moderations):
                moderations = Moderation.objects.filter(
                    type=COMPETE, moderator=profile, resolved=True, status=Code.APPROVED, competition__resultDeclared=True).order_by('-respondOn')
                cache.set(cachekey, moderations, settings.CACHE_INSTANT)
            data[Code.RESULTS] = results
            data[Code.JUDGEMENTS] = judements
            data[Code.MODERATIONS] = moderations
        elif section == profileString.ARTICLES:
            articles = cache.get(cachekey, [])
            if not len(articles):
                articles = Article.objects.filter(author=profile).order_by("-createdOn").distinct()
                cache.set(cachekey, articles, settings.CACHE_INSTANT)
            data[Code.PUBLISHED] = list(
                    filter(lambda p: not p.is_draft, articles))
            if selfprofile:
                data[Code.DRAFTED] = list(
                    filter(lambda p: p.is_draft, articles))
        elif section == profileString.FRAMEWORKS:
            frameworks = cache.get(cachekey, [])
            if not len(frameworks):
                if selfprofile:
                    frameworks = Framework.objects.filter(
                        creator=profile, trashed=False).order_by("-createdOn")
                else:
                    frameworks = Framework.objects.filter(
                        creator=profile, trashed=False, is_draft=False).order_by("-createdOn")
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
    except (KeyError, ValidationError, ObjectDoesNotExist):
        return False
    except Exception as e:
        errorLog(e)
        return False


def getProfileSectionHTML(profile: Profile, section: str, request: WSGIRequest) -> str:
    """Returns the text/HTML to render a profile section.

    Args:
        profile (Profile): The profile instance.
        section (str): The section to render.

    Returns:
        str: The text/HTML to render a profile section.
    """
    if section not in PROFILE_SECTIONS:
        return False
    data = dict()
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, profile, request.user)
            break
    return rendererstr(request, f"profile/{section}", data)


def getSettingSectionData(section: str, user: User, requestuser: User) -> dict:
    """Returns the context data to render a settings section.

    Args:
        section (str): The section to render.
        user (User): The user instance.
        requestuser (User): The requsting user instance

    Returns:
        dict: The context data to render a settings section.
    """
    data = dict()
    if not requestuser.is_authenticated:
        return data
    if section == profileString.Setting.ACCOUNT:
        pass
    if section == profileString.Setting.PREFERENCE:
        try:
            data[Code.SETTING] = ProfileSetting.objects.get(
                profile__user=user)
        except:
            pass
    if section == profileString.Setting.SECURITY:
        pass
    return data


def getSettingSectionHTML(user: User, section: str, request: WSGIRequest) -> str:
    """Returns the text/HTML to render a settings section.

    Args:
        user (User): The user instance.
        section (str): The section to render.
        request (WSGIRequest): The request object.

    Returns:
        str: The text/HTML to render a settings section.
    """
    if section not in SETTING_SECTIONS or request.user != user:
        return False
    data = dict()
    for sec in SETTING_SECTIONS:
        if sec == section:
            data = getSettingSectionData(sec, user, request.user)
            break
    return rendererstr(request, f"setting/{section}", data)


def getProfileImageBySocialAccount(socialaccount: SocialAccount) -> str:
    """
    Returns user profile third party account image URL by social account.

    Args:
        socialaccount (SocialAccount): The social account instance.

    Returns:
        str: The user profile third party account image URL, or default image URL.
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
                access_token: SocialToken = SocialToken.objects.get(
                    account=socialaccount, account__provider=LinkedInOAuth2Provider.id)
                resp = getRequest(f"https://api.linkedin.com/v2/me?projection=(profilePicture("
                                  f"displayImage~:playableStreams))&oauth2_access_token={access_token.token}")
                profile_pic_json = resp.json().get('profilePicture')
                elements = profile_pic_json['displayImage~']['elements']
                avatar = elements[-1]['identifiers'][0]['identifier']
        if avatar:
            return avatar
        return defaultImagePath()
    except:
        return defaultImagePath()


def isPictureSocialImage(picture: str) -> str:
    """
    If the given url points to a oauth provider account profile image, returns the provider id.

    Args:
        picture (str): The picture url.

    Returns:
        str: The matched provider id, or False.
    """
    if isPictureDeletable(picture):
        return False

    providerID = None
    for id in [DiscordProvider.id, GitHubProvider.id, GoogleProvider.id, LinkedInOAuth2Provider.id, "licdn.com"]:
        if id in str(picture):
            providerID = id
            break
    return providerID


def getUsernameFromGHSocial(ghSocial: SocialAccount) -> str or None:
    """
    Extracts github ID of user from their github profile url.

    Args:
        ghSocial (SocialAccount): The github social account instance.

    Returns:
        str: The github ID, or None.
    """
    try:
        return ghSocial.get_profile_url().split('/')[-1]
    except:
        return None


def topicProfilesList(profile: Profile, excludeUserIDs: list):
    """
    Updates present list of topic related profiles for given profile.
    """
    try:
        r = settings.REDIS_CLIENT
        if profile.totalAllTopics():
            topic = profile.getAllTopics()[0]
        else:
            topic = profile.recommended_topics()[0]
        r.set(f"{Browse.TOPIC_PROFILES}_{profile.id}_topic", topic)
        profiles = Profile.objects.filter(suspended=False, is_active=True, to_be_zombie=False, topics=topic).exclude(
            user__id__in=excludeUserIDs)
        profile_ids = [str(profile.id) for profile in profiles]
        if profile_ids:
            r.delete(f"{Browse.TOPIC_PROFILES}_{profile.id}")
            r.rpush(f"{Browse.TOPIC_PROFILES}_{profile.id}", *profile_ids)
    except Exception as e:
        errorLog(e)