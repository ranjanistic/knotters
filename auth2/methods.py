from compete.models import Competition
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http.response import HttpResponse
from django.utils import timezone
from main.methods import errorLog, renderString, renderView
from main.strings import Auth2, Code
from people.models import Profile, User
from projects.models import CoreProject, FreeProject, FreeRepository, Project

from .apps import APPNAME
from .models import DeviceNotification, EmailNotification, Notification


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    return renderString(request, file, data, fromApp=APPNAME)


def get_auth_section_data(requestUser: User, section: str):
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
        data['email_notifs'] = EmailNotification.objects.filter(
            subscribers=requestUser)
        data['device_notifs'] = DeviceNotification.objects.filter(
            subscribers=requestUser)
        pass
    return data


def get_auth_section_html(request: WSGIRequest, section: str):
    if section not in Auth2().AUTH2_SECTIONS:
        return False
    data = dict()
    for sec in Auth2().AUTH2_SECTIONS:
        if sec == section:
            data = get_auth_section_data(request.user, sec)
            break
    return renderer_stronly(request, section, data)


def migrateUserAssets(predecessor: User, successor: User) -> bool:
    try:
        if predecessor == successor:
            return True
        Project.objects.filter(Q(creator=predecessor.profile), Q(
            Q(status=Code.MODERATION) | Q(trashed=True))).delete()
        CoreProject.objects.filter(Q(creator=predecessor.profile), Q(
            Q(status=Code.MODERATION) | Q(trashed=True))).delete()
        FreeRepository.objects.filter(
            free_project__creator=predecessor.profile).delete()
        FreeProject.objects.filter(
            creator=predecessor.profile, trashed=True).delete()
        FreeProject.objects.filter(creator=predecessor.profile).update(
            migrated=True, migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)
        Project.objects.filter(creator=predecessor.profile).update(
            migrated=True, migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)
        Competition.objects.filter(
            creator=predecessor.profile, is_draft=True).delete()

        predprofile: Profile = predecessor.profile
        if predprofile.hasPredecessors():
            predprofile.predecessors().update(successor=successor)

        comps = Competition.objects.filter(creator=predecessor.profile)
        cprojs = CoreProject.objects.filter(
            creator=predecessor.profile, trashed=False)
        if len(comps) or len(cprojs):
            succprofile: Profile = successor.profile
            if not succprofile.is_manager():
                raise Exception(
                    "Cannot migrate competitions, successor is not manager.", predecessor, successor)
            else:
                comps.update(creator=succprofile)
                cprojs.update(migrated=True, migrated_by=predprofile,
                              migrated_on=timezone.now(), creator=succprofile)
        return True
    except Exception as e:
        errorLog(e)
        return False
