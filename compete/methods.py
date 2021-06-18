from django.template.loader import render_to_string
from main.methods import renderView
from main.strings import compete
from .apps import APPNAME


def renderer(request, file, data={}):
    return renderView(request, file, data,fromApp=APPNAME)


def competeBannerPath(instance, filename):
    return f"{APPNAME}/{instance.id}/{filename}"


def defaultBannerPath():
    return f"/{APPNAME}/default.png"


def getCompetitionSectionData(section, competition):
    if section == compete.OVERVIEW:
        return {}
    if section == compete.TASK:
        return {}
    if section == compete.GUIDELINES:
        return {}
    if section == compete.SUBMISSION:
        return {}
    if section == compete.RESULT:
        return {}


def getCompetitionSectionHTML(competition, section, request):
    if not compete.COMPETE_SECTIONS.__contains__(section):
        return False
    data = {}
    for sec in compete.COMPETE_SECTIONS:
        if sec == section:
            data = getCompetitionSectionData(sec, competition)
            break
    return render_to_string(f'{APPNAME}/profile/{section}.html',  data, request=request)
