from xmlrpc.client import Boolean
from compete.models import Competition
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import Q
from django.http.response import HttpResponse
from datetime import timedelta
from django.utils import timezone
from main.methods import (errorLog, renderString, renderView, addMethodToAsyncQueue, base64ToFile,
                          base64ToImageFile, errorLog, renderString,
                          respondJson, respondRedirect)
from main.strings import Auth2, Code, Message
from people.models import Profile, User
from projects.models import CoreProject, FreeProject, FreeRepository, Project, LeaveModerationTransferInvitation
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import JsonResponse
from projects.mailers import projectModTransferInvitation
from .apps import APPNAME
from .models import DeviceNotification, EmailNotification, Notification
from main.exceptions import InvalidUserOrProfile


def renderer(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Renders the text/html view for the auth section

    Args:
        request (WSGIRequest): The request object
        file (str): The file to render under the templates/auth2 directory, without extension
        data (dict, optional): The data to pass to the template

    Returns:
        str: The rendered text/html view with default and provided context
    """
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Get the text/html response for the auth section

    Args:
        request (WSGIRequest): The request object
        file (str): The file to render under the templates/auth2 directory, without extension
        data (dict, optional): The data to pass to the template

    Returns:
        str: The rendered text/html response with default and provided context
    """
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def renderer_stronly(request: WSGIRequest, file: str, data: dict = dict()) -> str:
    """Get the text/html string for the auth section

    Args:
        request (WSGIRequest): The request object
        file (str): The file to render under the templates/auth2 directory, without extension
        data (dict, optional): The data to pass to the template

    Returns:
        str: The rendered string based text/html with default and provided context
    """
    return renderString(request, file, data, fromApp=APPNAME)


def get_auth_section_data(requestUser: User, section: str) -> dict:
    """Get the context data for the auth section

    Args:
        requestUser (User): The user requesting the data
        section (str): The section to get data for

    Returns:
        dict: The data for the auth section
    """
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


def get_auth_section_html(request: WSGIRequest, section: str) -> str:
    """ Get the text/html string for the auth section

    Args:
        request (WSGIRequest): The request object
        section (str): The section to get

    Returns:
        str: The string based text/html
    """
    if section not in Auth2().AUTH2_SECTIONS:
        return False
    data = dict()
    for sec in Auth2().AUTH2_SECTIONS:
        if sec == section:
            data = get_auth_section_data(request.user, sec)
            break
    return renderer_stronly(request, section, data)


def migrateUserAssets(predecessor: User, successor: User) -> bool:
    """Migrate the assets of a user to another user, primarily used when deleting a user.

    Args:
        predecessor (User): The user to migrate assets from
        successor (User): The user to migrate assets to

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if predecessor == successor:
            return True
        predprofile: Profile = predecessor.profile
        if predprofile.hasPredecessors():
            predprofile.predecessors().update(successor=successor)

        comps = Competition.objects.filter(
            creator=predecessor.profile, is_draft=False)
        cprojs = CoreProject.objects.filter(
            creator=predecessor.profile, trashed=False, status__in={Code.APPROVED, Code.REJECTED})
        if len(comps) or len(cprojs):
            succprofile: Profile = successor.profile
            if not succprofile.is_manager():
                raise Exception(
                    "Cannot migrate competitions, successor is not manager.", predecessor, successor)
            else:
                comps.update(creator=succprofile)
                cprojs.update(migrated=True, migrated_by=predprofile,
                              migrated_on=timezone.now(), creator=succprofile)

        FreeRepository.objects.filter(
            free_project__creator=predecessor.profile).delete()
        FreeProject.objects.filter(creator=predecessor.profile, trashed=False).update(
            migrated=True, migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)
        Project.objects.filter(creator=predecessor.profile, trashed=False, status__in={Code.APPROVED, Code.REJECTED}).update(
            migrated=True, migrated_by=predecessor.profile, migrated_on=timezone.now(), creator=successor.profile)

        Project.objects.filter(Q(creator=predecessor.profile), Q(
            Q(status=Code.MODERATION) | Q(trashed=True))).delete()
        CoreProject.objects.filter(Q(creator=predecessor.profile), Q(
            Q(status=Code.MODERATION) | Q(trashed=True))).delete()
        FreeProject.objects.filter(
            creator=predecessor.profile, trashed=True).delete()
        Competition.objects.filter(
            creator=predecessor.profile, is_draft=True).delete()
        return True
    except Exception as e:
        errorLog(e)
        return False


def handleLeaveModInvitation(request: WSGIRequest, project, email) -> Boolean:
    """To handle Leave moderatorship invitation creation/deletion of a verified project

    METHODS: POST

    Args:
        request (WSGIRequest): The request object


    Returns:
        Boolean:  Returns true if task successful, or false
    """
    try:
        if (request.user.email == email) or (email in request.user.emails()):
            raise ObjectDoesNotExist(email)
        if project.moderator() != request.user.profile:
            raise ObjectDoesNotExist(request.user.profile)
        if not project.can_invite_mod():
            raise ObjectDoesNotExist("cannot invite mod: ", project)
        receiver = Profile.objects.get(
            user__email=email, is_moderator=True, is_mod_paused=False, suspended=False, is_active=True, to_be_zombie=False)
        if not project.can_invite_profile(receiver):
            raise InvalidUserOrProfile(receiver)

        if LeaveModerationTransferInvitation.objects.filter(baseproject=project.base(), receiver=receiver).exists():
            return False
        inv, created = LeaveModerationTransferInvitation.objects.get_or_create(
            project=project,
            sender=request.user.profile,
            resolved=False,
            defaults=dict(
                receiver=receiver,
                resolved=False
            )
        )
        inv: LeaveModerationTransferInvitation
        alert = True
        if not created:
            alert = False
            if inv.receiver != receiver:
                inv.receiver = receiver
                inv.expiresOn = timezone.now() + timedelta(days=1)
                inv.save()
                alert = True
        if alert:
            projectModTransferInvitation(inv)
    except (ObjectDoesNotExist, InvalidUserOrProfile):
        return False
    except Exception as e:
        errorLog(e)
        return False
