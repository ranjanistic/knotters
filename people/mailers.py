from typing_extensions import Self
from main.env import PUBNAME
from main.mailers import sendActionEmail
from main.strings import URL

from .models import ProfileTopic, User, Profile
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


def increaseXpAlert(profile: Profile, increment: int):
    """
    Send device notification to user when his Xp is increased
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.INCREASE_XP).exists():
        user_device_notify(profile.user, "Profile XP Increased!",
                           f"You have gained +{increment} XP!", profile.get_abs_link)


def decreaseXpAlert(profile: Profile, decrement: int):
    """
    Send device notification to user when his Xp is decreased
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.DECREASE_XP).exists():
        user_device_notify(profile.user, "Profile XP Decreased",
                           f"You have lost -{decrement} XP.", profile.get_abs_link)


def increaseBulkTopicXPAlert(profile: Profile, incrementbulk: int):
    """
    Send device notification to user when their Xp is increased in a topic
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.INCREASE_BULK_XP_TOPIC).exists():
        user_device_notify(profile.user, "Bulk Topics XP Increased!",
                           f"You have gained +{incrementbulk} XP in multiple topics at once!", profile.get_abs_link)


def increaseXPInTopicAlert(profile: ProfileTopic, incrementPoints: int, topicName: str, topicPoints: int):
    """
    Send device notification to user when their Xp is decreased in a topic 
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.profile.user, device_notification__notification__code=NotificationCode.INCREASE_XP_IN_TOPIC).exists():
        user_device_notify(profile.profile.user, "Topic XP increased.",
                           f"You have gained {incrementPoints} XP in {topicName}. {topicPoints} is your current XP.", profile.profile.get_abs_link)


def decreaseXPInTopicAlert(profile: ProfileTopic, decrementPoints: int, topicName: str, topicPoints: int):
    """
    Send device notification to user when their Xp is decreased in a topic 
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.profile.user, device_notification__notification__code=NotificationCode.DECREASE_XP_IN_TOPIC).exists():
        user_device_notify(profile.profile.user, "Topic XP decreased.",
                           f"You have lost -{decrementPoints} XP in {topicName}. {topicPoints} is your current XP.", profile.profile.get_abs_link)


def milestoneNotif(profile: Profile):
    """
    Check the milestone status of the user and accordingly send a notification
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.MILESTONE_NOTIF).exists():
        user_device_notify(profile.user, "Milestone achieved",
                           f"You have achieved a milestone for earning { 50*(1+pow(profile.milestone_count, 2))} XP congratulations!", profile.get_abs_link)

    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.MILESTONE_NOTIF).exists():
        sendActionEmail(
            to=profile.getEmail(),
            username=profile.getFName(),
            subject='Milestone Achieved!',
            header=f"Yay! You have successfully achieved a milestone for earning { 50*(1+pow(profile.milestone_count, 2))} XP. You can view your your profile by clicking the link",
            actions=[{
                'text': 'View Profile',
                'url': profile.get_abs_link
            }],
            footer=f"You can visit your profile and view your XP by clicking this link",
            conclusion=f"This email was sent to you because you have subscibed to milestone notifications on our webiste"
        )


def milestoneNotifTopic(profile: ProfileTopic):
    """
    Check the milestone status of the user and accordingly send a notification
    """
    if DeviceNotificationSubscriber.objects.filter(user=profile.profile.user, device_notification__notification__code=NotificationCode.MILESTONE_NOTIF_TOPIC).exists():
        user_device_notify(profile.profile.user, "Milestone achieved",
                           f"You have achieved a milestone for earning { 50*(1+pow(profile.milestone_count_topic, 2))} XP congratulations!", profile.profile.get_abs_link)

    if EmailNotificationSubscriber.objects.filter(user=profile.profile.user, email_notification__notification__code=NotificationCode.MILESTONE_NOTIF_TOPIC).exists():
        sendActionEmail(
            to=profile.profile.getEmail(),
            username=profile.profile.getFName(),
            subject='Milestone Achieved!',
            header=f"Yay! You have successfully achieved a milestone for earning { 50*(1+pow(profile.milestone_count_topic, 2))} XP. You can view your your profile by clicking the link",
            actions=[{
                'text': 'View Profile',
                'url': profile.profile.get_abs_link
            }],
            footer=f"You can visit your profile and view your XP by clicking this link",
            conclusion=f"This email was sent to you because you have subscibed to milestone notifications on our webiste"
        )
