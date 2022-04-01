from uuid import UUID
from django.core.exceptions import ObjectDoesNotExist
from django.core.handlers.wsgi import WSGIRequest
from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import redirect
from django.http.response import Http404, HttpResponse, JsonResponse
from allauth.account.decorators import login_required
from main.env import BOTMAIL
from main.strings import Action, Message, Template, Code
from main.decorators import manager_only, normal_profile_required, require_JSON
from main.methods import addMethodToAsyncQueue, errorLog, respondJson, user_device_notify
from people.models import Profile, User
from management.models import Management
from .mailers import accountInactiveAlert, accountReactiveAlert, successorAccepted, successorDeclined, successorInvite
from .models import DeviceNotification, EmailNotification
from .methods import get_auth_section_html, migrateUserAssets, renderer
from .apps import APPNAME


@normal_profile_required
def notification_enabled(request: WSGIRequest) -> HttpResponse:
    user_device_notify(
        request.user, body='You have successfully enabled notifications.', title='Notifications Enabled')
    return respondJson(Code.OK)


@normal_profile_required
@require_GET
def auth_index(request: WSGIRequest):
    return renderer(request, Template.Auth.INDEX)


@normal_profile_required
@require_GET
def auth_index_tab(request: WSGIRequest, section: str):
    try:
        data = get_auth_section_html(request, section)
        if data:
            return HttpResponse(data)
        else:
            raise Exception('No section data')
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def verify_authorization_method(request: WSGIRequest):
    try:
        methods = []
        if request.user.has_usable_password():
            methods.append('password')
        if request.user.has_totp_device_enabled():
            methods.append('totp')
        return respondJson(Code.OK, dict(methods=methods))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)

@normal_profile_required
@require_JSON
def verify_authorization(request: WSGIRequest):
    try:
        password = request.POST.get('password', None)
        totp = request.POST.get('totp', None)
        verified = False
        if password and totp:
            verified = request.user.check_password(password) and request.user.verify_totp(totp)
        elif password:
            verified = request.user.check_password(password)
        elif totp:
            verified = request.user.verify_totp(totp)
        if verified:
            return respondJson(Code.OK)
        return respondJson(Code.NO, error=Message.INVALID_CREDENTIALS)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)


@manager_only
@require_JSON
def change_ghorg(request: WSGIRequest):
    try:
        newghorgID = request.POST['newghorgID']
        if newghorgID == False:
            mgm = request.user.profile.update_management(githubOrgID=None)
        elif newghorgID not in map(lambda id: str(id), request.user.profile.get_ghOrgIDs()):
            raise ObjectDoesNotExist(newghorgID)
        else:
            mgm = request.user.profile.update_management(
                githubOrgID=str(newghorgID))
        if mgm:
            return respondJson(Code.OK)
        return respondJson(Code.NO)
    except (ObjectDoesNotExist, KeyError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)



@login_required
@require_JSON
def accountActivation(request: WSGIRequest) -> JsonResponse:
    """
    Activate or deactivate account.
    Does not delete anything, just meant to hide profile from the world whenever the requesting user wants.
    """
    activate = request.POST.get('activate', None)
    deactivate = request.POST.get('deactivate', None)
    try:
        if activate == deactivate:
            raise ObjectDoesNotExist()
        if activate and not request.user.profile.is_active:
            is_active = True
        elif deactivate and request.user.profile.is_active:
            is_active = False
        else:
            raise ObjectDoesNotExist()
        if is_active and request.user.profile.suspended:
            raise ObjectDoesNotExist()

        done = Profile.objects.filter(
            user=request.user).update(is_active=is_active)
        if not done:
            return respondJson(Code.NO)
        if is_active:
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{accountReactiveAlert.__name__}", request.user.profile)
        else:
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{accountInactiveAlert.__name__}", request.user.profile)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def profileSuccessor(request: WSGIRequest):
    """
    To set/modify/unset profile successor. If default is chosen by the requestor, then sets the default successor and successor confirmed as true.
    Otherwise, updates successor and sends invitation email to successor if set, and sets successor confirmed as false,
    which will change only when the invited successor acts on invitation.
    """
    set = request.POST.get('set', None)
    userID = request.POST.get('userID', None)
    usedefault = request.POST.get('useDefault', False)
    unset = request.POST.get('unset', None)

    try:
        if set == unset:
            return respondJson(Code.NO)
        successor = None
        if set:
            if usedefault or userID == BOTMAIL:
                try:
                    successor = User.objects.get(email=BOTMAIL)
                    successor_confirmed = True
                except Exception as e:
                    errorLog(e)
                    return respondJson(Code.NO)
            elif userID and request.user.email != userID and not (userID in request.user.emails()):
                try:
                    if request.user.profile.is_manager():
                        smgm = Management.objects.get(profile__user__email=userID)
                        successor = smgm.profile.user
                    else:
                        successor = User.objects.get(
                            email=userID)

                    if successor.profile.isBlocked(request.user):
                        return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
                    if not successor.profile.ghID() and not successor.profile.githubID:
                        return respondJson(Code.NO, error=Message.SUCCESSOR_GH_UNLINKED)
                    if successor.profile.successor == request.user:
                        if not successor.profile.successor_confirmed:
                            addMethodToAsyncQueue(
                                f"{APPNAME}.mailers.{successorInvite.__name__}", request.user, successor)
                        return respondJson(Code.NO, error=Message.SUCCESSOR_OF_PROFILE)
                    successor_confirmed = userID == BOTMAIL
                except Exception as e:
                    return respondJson(Code.NO, error=Message.SUCCESSOR_NOT_FOUND)
            else:
                raise ObjectDoesNotExist()
        elif unset and request.user.profile.successor:
            successor = None
            successor_confirmed = False
        else:
            raise ObjectDoesNotExist()
        Profile.objects.filter(user=request.user).update(
            successor=successor, successor_confirmed=successor_confirmed)
        if successor and not successor_confirmed:
            addMethodToAsyncQueue(
                f"{APPNAME}.mailers.{successorInvite.__name__}", successor, request.user)
        return respondJson(Code.OK)
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def getSuccessor(request: WSGIRequest) -> JsonResponse:
    if request.user.profile.successor:
        return respondJson(Code.OK, dict(
            successorID=(
                request.user.profile.successor.email if request.user.profile.successor.email != BOTMAIL else '')
        ))
    return respondJson(Code.NO)


@normal_profile_required
@require_GET
def successorInvitation(request: WSGIRequest, predID: UUID) -> HttpResponse:
    """
    Render profile successor invitation view.
    """
    try:
        predecessor = User.objects.get(id=predID)
        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise ObjectDoesNotExist(predecessor.profile.successor)
        return renderer(request, Template.Auth.INVITATION, dict(predecessor=predecessor))
    except ObjectDoesNotExist as e:
        raise Http404(e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_POST
def successorInviteAction(request: WSGIRequest, action: str) -> HttpResponse:
    """
    Sets the successor if accepted, or sets default successor.
    Also deletes the predecessor account and migrates assets, only if it was scheduled to be deleted.
    """
    predID = request.POST.get('predID', None)
    accept = action == Action.ACCEPT

    try:
        if (not accept and action != Action.DECLINE) or not predID or predID == request.user.getID():
            raise ObjectDoesNotExist(action, predID)

        predecessor = User.objects.get(id=predID)

        if predecessor.profile.successor != request.user or predecessor.profile.successor_confirmed:
            raise ObjectDoesNotExist(predecessor.profile, request.user, predecessor.profile.successor)

        if accept:
            successor = request.user
            predecessor.profile.successor_confirmed = True
        else:
            if predecessor.profile.to_be_zombie:
                successor = User.objects.get(email=BOTMAIL)
                predecessor.profile.successor_confirmed = True
            else:
                successor = None

        predecessor.profile.successor = successor
        predecessor.profile.save()

        deleted = False
        if predecessor.profile.to_be_zombie:
            migrateUserAssets(predecessor, successor)
            predecessor.delete()
            deleted = True

        if accept:
            alert = Message.SUCCESSORSHIP_ACCEPTED
            if not deleted:
                addMethodToAsyncQueue(
                    f"{APPNAME}.mailers.{successorAccepted.__name__}", successor, predecessor)
        else:
            alert = Message.SUCCESSORSHIP_DECLINED
            if not deleted:
                addMethodToAsyncQueue(
                    f"{APPNAME}.mailers.{successorDeclined.__name__}", request.user, predecessor)
        if not deleted:
            return redirect(predecessor.profile.getLink(alert=alert))
        return redirect(request.user.profile.getLink(alert=alert))
    except ObjectDoesNotExist as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def accountDelete(request: WSGIRequest) -> JsonResponse:
    """
    Account for deletion, only if a successor is set.
    If successor has not been confirmed yet,
    then just schedules account to be deleted at the moment the successor is confirmed.
    Otherwise, deletes the account and makes the profile a zombie.

    For the requesting user, successfull response of this endpoint should imply permanent inaccess to their account,
    regardless of successor confirmation state.
    """
    confirmed = request.POST.get('confirmed', False)
    if not confirmed:
        return respondJson(Code.NO)
    if not request.user.profile.successor:
        return respondJson(Code.NO, error=Message.SUCCESSOR_UNSET)
    try:
        done = Profile.objects.filter(
            user=request.user).update(to_be_zombie=True)
        User.objects.filter(id=request.user.id).update(is_active=False)
        if request.user.profile.successor_confirmed:
            user = User.objects.get(id=request.user.id)
            migrateUserAssets(user, user.profile.successor)
            user.delete()
        return respondJson(Code.OK if done else Code.NO, message=Message.ACCOUNT_DELETED)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO)



@normal_profile_required
@require_JSON
def email_notification_toggle(request: WSGIRequest, notifID: UUID):
    try:
        subscribe = request.POST['subscribe']
        denotif = EmailNotification.objects.get(notification__id=notifID)
        if not subscribe:
            denotif.subscribers.remove(request.user)
        else:
            denotif.subscribers.add(request.user)
        return respondJson(Code.OK)
    except (KeyError, ObjectDoesNotExist) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def device_notifcation_toggle(request: WSGIRequest, notifID: UUID):
    try:
        subscribe = request.POST['subscribe']
        denotif = DeviceNotification.objects.get(notification__id=notifID)
        if not subscribe:
            denotif.subscribers.remove(request.user)
        else:
            denotif.subscribers.add(request.user)
        return respondJson(Code.OK)
    except (KeyError, ObjectDoesNotExist) as o:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
