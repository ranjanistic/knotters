from typing_extensions import Self
from main.env import PUBNAME
from main.mailers import sendActionEmail
from main.strings import URL

from .models import User
from main.methods import user_device_notify
from auth2.models import *
from main.constants import NotificationCode
from main.mailers import sendActionEmail


def welcomeAlert(user: User) -> str:
    """
    Send an email to a new user with a welcome message.
    """
    return sendActionEmail(
        to=user.email,
        username=user.getName(),
        greeting='Welcome',
        subject=f"Welcome to {PUBNAME} Community",
        header="We're pleased to let you know that you're now a part of our booming community! This comes with lot of opportunities "
        "to create, learn and contribute towards the betterment of everyone.",
        actions=[dict(
            text='Get started',
            url=f"/{URL.HOME}"
        )],
        footer="Please do not hesitate if you have any doubts or queries to ask. Do checkout our social channels (links below) for direct interactions.",
        conclusion=f"This email was sent because you created an account on {PUBNAME}. If there's a problem, then please report to us."
    )


def Increase_Xp_Alert(user, increment, profile_link):
    if DeviceNotificationSubscriber.objects.filter(user=user, device_notification__notification__code=NotificationCode.INCREASE_XP).exists():
        user_device_notify(user, "Profile XP Increased!",
                           f"You have gained +{increment} XP!", profile_link)


def Decrease_Xp_Alert(user, decrement, profile_link):
    if DeviceNotificationSubscriber.objects.filter(user=user, device_notification__notification__code=NotificationCode.DECREASE_XP).exists():
        user_device_notify(user, "Profile XP Decreased",
                           f"You have lost -{decrement} XP.", profile_link)


def Increase_Bulk_Topic_XP_Alert(user, IncrementBulk, profile_link):
    if DeviceNotificationSubscriber.objects.filter(user=user, device_notification__notification__code=NotificationCode.INCREASE_BULK_XP_TOPIC).exists():
        user_device_notify(user, "Bulk Topics XP Increased!",
                           f"You have gained +{IncrementBulk} XP in multiple topics at once!", profile_link)
