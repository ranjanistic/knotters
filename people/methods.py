from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.github.provider import GitHubProvider
from allauth.socialaccount.providers.google.provider import GoogleProvider
from allauth.socialaccount.providers.discord.provider import DiscordProvider
from main.methods import errorLog, renderData, renderString, renderView
from main.strings import URL, Code, profile as profileString
from projects.models import Project
from moderation.models import Moderation
from .models import ProfileSetting, User, Profile
from .apps import APPNAME


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, dict(**data, URLS=URL.people.getURLSForClient()), fromApp=APPNAME)

def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderString(request, file, dict(**data, URLS=URL.people.getURLSForClient()), fromApp=APPNAME)

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
    if len(bio) > 120:
        bio = bio[:(120-len(bio))]
        return filterBio(bio)
    return bio


PROFILE_SECTIONS = [profileString.OVERVIEW, profileString.PROJECTS,
                    profileString.CONTRIBUTION, profileString.ACTIVITY, profileString.MODERATION]

SETTING_SECTIONS = [profileString.setting.ACCOUNT,
                    profileString.setting.PREFERENCE]


def getProfileSectionData(section: str, profile: Profile, requestUser: User) -> dict:
    data = dict(
            self=requestUser == profile.user,
            person=profile.user
        )
    if section == profileString.OVERVIEW:
        pass
    elif section == profileString.PROJECTS:
        if requestUser == profile.user:
            projects = Project.objects.filter(creator=profile)
        else:
            projects = Project.objects.filter(
                creator=profile, status=Code.APPROVED)
        data[Code.APPROVED] = projects.filter(status=Code.APPROVED)
        data[Code.MODERATION] = projects.filter(status=Code.MODERATION)
        data[Code.REJECTED] = projects.filter(status=Code.REJECTED)
    elif section == profileString.CONTRIBUTION:
        pass
    elif section == profileString.ACTIVITY:
        pass
    elif section == profileString.MODERATION:
        if profile.is_moderator:
            mods = Moderation.objects.filter(moderator=profile)
            data[Code.RESOLVED] = mods.filter(resolved=True)
            data[Code.UNRESOLVED] = mods.filter(resolved=False)
    else: return False
    return data


def getProfileSectionHTML(profile: Profile, section: str, request: WSGIRequest) -> str:
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = dict()
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, profile, request.user)
            break
    return rendererstr(request,f"profile/{section}", data)


def getSettingSectionData(section: str, user: User, requestuser: User) -> dict:
    data = dict()
    if not requestuser.is_authenticated: return data
    if section == profileString.Setting.ACCOUNT:
        pass
    if section == profileString.Setting.PREFERENCE:
        try:
            data[Code.SETTING] = ProfileSetting.objects.get(profile=user.profile)
        except:
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
    return rendererstr(request,f"setting/{section}", data)


def getProfileImageBySocialAccount(socialaccount: SocialAccount) -> str:
    """
    Returns user profile image url by social account.
    """
    if socialaccount.provider == GitHubProvider.id:
        return socialaccount.extra_data['avatar_url']
    if socialaccount.provider == GoogleProvider.id:
        link = str(socialaccount.extra_data['picture'])
        linkpart = link.split("=")[0]
        sizesplit = link.split("=")[1].split("-")
        sizesplit.remove(sizesplit[0])
        return "=".join([linkpart, "-".join(["s512", "-".join(sizesplit)])])
    if socialaccount.provider == DiscordProvider.id:
        return f"https://cdn.discordapp.com/avatars/{socialaccount.uid}/{socialaccount.extra_data['avatar']}.png?size=1024"
    return defaultImagePath()


def isPictureDeletable(picture: str) -> bool:
    """
    Checks whether the given profile picture is stored in web server storage separately, and therefore can be deleted or not.
    """
    return picture != defaultImagePath() and not str(picture).startswith('http')

def isPictureSocialImage(picture: str) -> str:
    """
    If the given url points to a oauth provider account profile image, returns the provider id.
    """
    if isPictureDeletable(picture): return False

    providerID = None
    for id in [DiscordProvider.id, GitHubProvider.id, GoogleProvider.id]:
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


def migrateUserAssets(predecessor: User, successor: User) -> bool:
    try:
        if predecessor == successor: return True
        Project.objects.filter(creator=predecessor.profile,
                               status=Code.MODERATION).delete()
        Project.objects.filter(creator=predecessor.profile, status__in=[
                               Code.APPROVED, Code.REJECTED]).update(migrated=True, creator=successor.profile)
        return True
    except Exception as e:
        errorLog(e)
        return False

from .receivers import *