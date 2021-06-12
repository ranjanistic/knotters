from main.methods import renderView
from .apps import APPNAME
from project.models import Project
from .apps import APPNAME
from main.strings import code, profile
from django.template.loader import render_to_string


def renderer(request, file, data={}):
    data['root'] = f"/{APPNAME}"
    data['subappname'] = APPNAME
    return renderView(request, f"{APPNAME}/{file}", data)


def profileImagePath(instance, filename):
    return f"{APPNAME}/{instance.id}/profile/{filename}"


def defaultImagePath():
    return f"/{APPNAME}/default.png"

    
PROFILE_SECTIONS = [profile.OVERVIEW, profile.PROJECTS,
                    profile.CONTRIBUTION, profile.ACTIVITY, profile.MODERATION]


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


def getProfileSectionHTML(user, section):
    if not PROFILE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in PROFILE_SECTIONS:
        if sec == section:
            data = getProfileSectionData(sec, user)
            break
    return render_to_string(f'{APPNAME}/section/{section}.html',  data)
