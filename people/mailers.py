# TODO Set email triggers

from main.mailers import sendAlertEmail, sendActionEmail
from .models import User, Profile

def passordChangeAlert(user:User) -> bool:
    print('account password changed')
    return True

def emailUpdateAlert(user:User) -> bool:
    print('account email updated deactivated')
    return True

def accountInactiveAlert(profile: Profile) -> bool:
    print('account deactivated')
    return True

def accountReactiveAlert(profile: Profile) -> bool:
    print('account re activated')
    return True

def accountDeleteAlert(user: User) -> bool:
    print('account deleted successfully')
    return True

def successorInvite(successor: User, predecessor: User) -> bool:
    print('successor invited successfully')
    print(predecessor.profile.getSuccessorInviteLink())
    return True
