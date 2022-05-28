from typing_extensions import Self
from main.env import PUBNAME
from main.mailers import sendActionEmail
from main.strings import URL

from .models import User, Profile
from main.methods import user_device_notify
from auth2.models import *
from main.constants import NotificationCode


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


def Increase_Xp_Alert(profile: Profile, increment: int):
    """
    Send device notification to user when his Xp is increased
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.INCREASE_XP).exists():
        user_device_notify(profile.user, "Profile XP Increased!",
                           f"You have gained +{increment} XP!", profile.get_abs_link)


def Decrease_Xp_Alert(profile: Profile, decrement: int):
    """
    Send device notification to user when his Xp is decreased
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.DECREASE_XP).exists():
        user_device_notify(profile.user, "Profile XP Decreased",
                           f"You have lost -{decrement} XP.", profile.get_abs_link)


def Increase_Bulk_Topic_XP_Alert(profile: Profile, incrementbulk: int):
    """
    Send device notification to user when his Xp is increased in bulk
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.INCREASE_BULK_XP_TOPIC).exists():
        user_device_notify(profile.user, "Bulk Topics XP Increased!",
                           f"You have gained +{incrementbulk} XP in multiple topics at once!", profile.get_abs_link)