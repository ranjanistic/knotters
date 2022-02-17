from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse
from people.models import User
from webpush.models import Group
from main.strings import Code, Template, Auth2
from projects.models import CoreProject, Project, FreeProject, FreeRepository
from compete.models import Competition
from main.methods import renderString, renderView
from .models import DeviceNotification, EmailNotification, Notification
from .apps import APPNAME
from .receivers import *

def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))

def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    return renderString(request, file, data, fromApp=APPNAME)

def get_auth_section_data(requestUser, section):
    data = dict()
    if section == Auth2.DEVICE:
        pass
    if section == Auth2.ACCOUNT:
        pass
    if section == Auth2.SECURITY:
        pass
    if section == Auth2.PREFERENCE:
        pass
    if section == Auth2.NOTIFICATION:
        data['notifications'] = Notification.objects.filter(disabled=False)
        data['email_notifs'] = EmailNotification.objects.filter(subscribers=requestUser)
        data['device_notifs'] = DeviceNotification.objects.filter(subscribers=requestUser)
        pass
    return data
    
def get_auth_section_html(request, section):
    if section not in Auth2().AUTH2_SECTIONS:
        return False
    data = dict()
    for sec in Auth2().AUTH2_SECTIONS:
        if sec == section:
            data = get_auth_section_data(request.user,sec)
            break
    return renderer_stronly(request, section, data)

def migrateUserAssets(predecessor: User, successor: User) -> bool:
    try:
        if predecessor == successor: return True
        Project.objects.filter(creator=predecessor.profile,status=Code.MODERATION).delete()
        CoreProject.objects.filter(creator=predecessor.profile,status=Code.MODERATION).delete()
        FreeRepository.objects.filter(free_project__creator=predecessor.profile).delete()
        FreeProject.objects.filter(creator=predecessor.profile,trashed=False).update(migrated=True,migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)
        Project.objects.filter(creator=predecessor.profile,trashed=False).update(migrated=True,migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)

        if predecessor.profile.hasPredecessors():
            predecessor.profile.predecessors().update(successor=successor)

        comps = Competition.objects.filter(creator=predecessor.profile)
        if len(comps):
            if successor.profile.is_manager():
                comps.update(creator=successor.profile)
            else:
                raise Exception("Cannot migrate competitions, successor is not manager.", predecessor, successor)
        cprojs = CoreProject.objects.filter(creator=predecessor.profile,trashed=False)
        if len(cprojs):
            if successor.profile.is_manager():
                cprojs.update(migrated=True,migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)
            else:
                raise Exception("Cannot migrate core projects, successor is not manager.", predecessor, successor)
        return True
    except Exception as e:
        errorLog(e)
        return False
