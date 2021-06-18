from main.methods import renderView
from .apps import APPNAME
from projects.models import Project
from .apps import APPNAME
from main.strings import code, profile
from django.template.loader import render_to_string


def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


def convertToFLname(string):
    name = str(string).title()
    namesequence = name.split(" ")
    firstname = namesequence[0]
    del namesequence[0]
    if len(namesequence) > 0:
        lastname = " ".join(namesequence)
    else:
        lastname = ''
    return firstname, lastname

def profileImagePath(instance, filename):
    return f"{APPNAME}/{instance.id}/profile/{filename}"


def defaultImagePath():
    return f"/{APPNAME}/default.png"


PROFILE_SECTIONS = [profile.OVERVIEW, profile.PROJECTS,
                    profile.CONTRIBUTION, profile.ACTIVITY, profile.MODERATION]

SETTING_SECTIONS = [profile.setting.ACCOUNT, profile.setting.PREFERENCE]


def getProfileSectionData(section, user):
    if section == profile.OVERVIEW:
        return {}
    if section == profile.PROJECTS:
        projects = Project.objects.filter(creator=user)
        return {
            code.LIVE: projects.filter(status=code.LIVE),
            code.MODERATION: projects.filter(status=code.MODERATION),
            code.REJECTED: projects.filter(status=code.REJECTED),
        }
    if section == profile.CONTRIBUTION:
        return {}
    if section == profile.ACTIVITY:
        return {}
    if section == profile.MODERATION:
        return {}


def getSettingSectionData(section, user):
    if section == profile.OVERVIEW:
        return {}
    if section == profile.PROJECTS:
        projects = Project.objects.filter(creator=user)
        return {
            code.LIVE: projects.filter(status=code.LIVE),
            code.MODERATION: projects.filter(status=code.MODERATION),
            code.REJECTED: projects.filter(status=code.REJECTED),
        }
    if section == profile.CONTRIBUTION:
        return {}
    if section == profile.ACTIVITY:
        return {}
    if section == profile.MODERATION:
        return {}


def getProfileSectionHTML(user, section, request):
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, user)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)


def getSettingSectionHTML(user, section, request):
    if not SETTING_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in SETTING_SECTIONS:
        if sec == section:
            data = getSettingSectionData(sec, user)
            break
    return render_to_string(f'{APPNAME}/setting/{section}.html',  data, request=request)
