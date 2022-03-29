from django.urls import path
from main.strings import URL
# import mfa
# import mfa.TrustedDevice
from .views import *

urlpatterns = [
    # path('mfa/', include('mfa.urls')),
    # path('devices/add/', mfa.TrustedDevice.add,name="mfa_add_new_trusted_device"),
    path(URL.INDEX, auth_index),
    path(URL.Auth.NOTIF_ENABLED, notification_enabled),
    path(URL.Auth.TAB_SECTION, auth_index_tab),
    path(URL.Auth.VERIFY_REAUTH_METHOD, verify_authorization_method),
    path(URL.Auth.VERIFY_REAUTH, verify_authorization),
    path(URL.Auth.CHANGE_GHORG, change_ghorg),
    path(URL.Auth.ACCOUNTACTIVATION, accountActivation),
    path(URL.Auth.GETSUCCESSOR, getSuccessor),
    path(URL.Auth.INVITESUCCESSOR, profileSuccessor),
    path(URL.Auth.SUCCESSORINVITE, successorInvitation),
    path(URL.Auth.SUCCESSORINVITEACTION, successorInviteAction),
    path(URL.Auth.ACCOUNTDELETE, accountDelete),
    path(URL.Auth.NOTIFICATION_TOGGLE_EMAIL, email_notification_toggle),
    path(URL.Auth.NOTIFICATION_TOGGLE_DEVICE, device_notifcation_toggle),
]
