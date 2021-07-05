from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from django.template.loader import render_to_string
from main.methods import renderData, renderView
from main.strings import code, profile as profileString
from projects.models import Project
from moderation.models import Moderation
from .models import ProfileSetting, User, Profile
from .apps import APPNAME
from .receivers import *


def renderer(request: WSGIRequest, file: str, data: dict = {}) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)

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
        lastname = ''
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


def getProfileSectionData(section: str, profile: Profile, request: WSGIRequest) -> dict:
    data = renderData({
        'self': request.user == profile.user,
        'person': profile.user
    }, APPNAME)
    if section == profileString.OVERVIEW:
        pass
    if section == profileString.PROJECTS:
        if request.user == profile.user:
            projects = Project.objects.filter(creator=profile)
        else:
            projects = Project.objects.filter(
                creator=profile, status=code.LIVE)
        data[code.LIVE] = projects.filter(status=code.APPROVED)
        data[code.MODERATION] = projects.filter(status=code.MODERATION)
        data[code.REJECTED] = projects.filter(status=code.REJECTED)
        pass
    if section == profileString.CONTRIBUTION:
        pass
    if section == profileString.ACTIVITY:
        pass
    if section == profileString.MODERATION:
        if profile.is_moderator:
            mods = Moderation.objects.filter(moderator=profile)
            data['resolved'] = mods.filter(resolved=True)
            data['unresolved'] = mods.filter(resolved=False)
    return data


def getProfileSectionHTML(profile: Profile, section: str, request: WSGIRequest) -> str:
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, profile, request)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)


def getSettingSectionData(section: str, user: User, request: WSGIRequest) -> dict:
    data = renderData(fromApp=APPNAME)
    if section == profileString.setting.ACCOUNT:
        pass
    if section == profileString.setting.PREFERENCE:
        try:
            data['setting'] = ProfileSetting.objects.get(profile=user.profile)
        except:
            pass
    return data


def getSettingSectionHTML(user: User, section: str, request: WSGIRequest) -> str:
    if not SETTING_SECTIONS.__contains__(section) or request.user != user:
        return False
    data = {}
    for sec in SETTING_SECTIONS:
        if sec == section:
            data = getSettingSectionData(sec, user, request)
            break
    return render_to_string(f'{APPNAME}/setting/{section}.html',  data, request=request)
