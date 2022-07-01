from main.env import PUBNAME
from main.mailers import sendActionEmail
from main.strings import URL

from .models import ProfileTopic, User, Profile
from main.methods import user_device_notify
from auth2.models import *
from main.constants import NotificationCode
from management.models import ReportCategory
from django.core.handlers.wsgi import WSGIRequest


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
    Send device notification to user when their Xp is increased
    """
    device = False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.INCREASE_XP).exists():
        device = user_device_notify(profile.user, "Profile XP Increased!",
                           f"You have gained +{increment} XP!", profile.get_abs_link)
    return device


def decreaseXpAlert(profile: Profile, decrement: int):
    """
    Send device notification to user when their Xp is decreased
    """
    device = False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.DECREASE_XP).exists():
        device = user_device_notify(profile.user, "Profile XP Decreased",
                           f"You have lost -{decrement} XP.", profile.get_abs_link)
    return device


def increaseBulkTopicXPAlert(profile: Profile, incrementbulk: int):
    """
    Send device notification to user when their Xp is increased in a topic
    """
    device = False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.INCREASE_BULK_XP_TOPIC).exists():
        device = user_device_notify(profile.user, "Bulk Topics XP Increased!",
                           f"You have gained +{incrementbulk} XP in multiple topics at once!", profile.get_abs_link)
    return device


def increaseXPInTopicAlert(profile: ProfileTopic, incrementPoints: int, topicName: str, topicPoints: int):
    """
    Send device notification to user when their Xp is decreased in a topic 
    """
    device = False
    if DeviceNotificationSubscriber.objects.filter(user=profile.profile.user, device_notification__notification__code=NotificationCode.INCREASE_XP_IN_TOPIC).exists():
        device = user_device_notify(profile.profile.user, "Topic XP increased.",
                           f"You have gained {incrementPoints} XP in {topicName}. {topicPoints} is your current XP.", profile.profile.get_abs_link)
    return device


def decreaseXPInTopicAlert(profile: ProfileTopic, decrementPoints: int, topicName: str, topicPoints: int):
    """
    Send device notification to user when their Xp is decreased in a topic 
    """
    device = False
    if DeviceNotificationSubscriber.objects.filter(user=profile.profile.user, device_notification__notification__code=NotificationCode.DECREASE_XP_IN_TOPIC).exists():
        device = user_device_notify(profile.profile.user, "Topic XP decreased.",
                           f"You have lost -{decrementPoints} XP in {topicName}. {topicPoints} is your current XP.", profile.profile.get_abs_link)
    return device


def milestoneNotif(profile: Profile):
    """
    Check the milestone status of the user and accordingly send a notification
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.MILESTONE_NOTIF).exists():
        device = user_device_notify(profile.user, "Milestone achieved",
                           f"You have achieved a milestone for earning { 50*(1+pow(profile.milestone_count, 2))} XP congratulations!", profile.get_abs_link)

    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.MILESTONE_NOTIF).exists():
        email = sendActionEmail(
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
    return device, email


def milestoneNotifTopic(profileTopic: ProfileTopic):
    """
    Check the milestone status of the user and accordingly send a notification
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profileTopic.profile.user, device_notification__notification__code=NotificationCode.MILESTONE_NOTIF_TOPIC).exists():
        device = user_device_notify(profileTopic.profile.user, "Milestone achieved",
                           f"You have achieved a milestone for earning { 50*(1+pow(profileTopic.milestone_count_topic, 2))} XP congratulations!", profileTopic.profile.get_abs_link)

    if EmailNotificationSubscriber.objects.filter(user=profileTopic.profile.user, email_notification__notification__code=NotificationCode.MILESTONE_NOTIF_TOPIC).exists():
        email = sendActionEmail(
            to=profileTopic.profile.getEmail(),
            username=profileTopic.profile.getFName(),
            subject='Milestone Achieved!',
            header=f"Yay! You have successfully achieved a milestone for earning { 50*(1+pow(profileTopic.milestone_count_topic, 2))} XP. You can view your your profile by clicking the link",
            actions=[{
                'text': 'View Profile',
                'url': profileTopic.profile.get_abs_link
            }],
            footer=f"You can visit your profile and view your XP by clicking this link",
            conclusion=f"This email was sent to you because you have subscibed to milestone notifications on our webiste"
        )
    return device, email


def reportedUser(user: User, category: ReportCategory):
    """
    Alert the user that they have been reported.
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=user, device_notification__notification__code=NotificationCode.REPORTED_USER).exists():
        device = user_device_notify(user, "Report Alert",
                           f"You have been reported for {category}. The complaint is under review.",
                           user.getLink())
    if EmailNotificationSubscriber.objects.filter(user=user, email_notification__notification__code=NotificationCode.REPORTED_USER).exists():
        email = sendActionEmail(
            to=user.email, username=user.first_name, subject='Reported for Misconduct',
            header=f"This is to inform you that you have been reported for {category}. The report is under review.",
            actions=[{'text': "View Profile",
                      'url': user.getLink()}],
            footer=f"Knotters is a place for creating community and belonging. To avoid future reports against you, make sure you read and understand Knotters terms and conditions.",
            conclusion=f"If you think this is a mistake, please report to us."
        )
    return device, email


def admireAlert(profile: Profile, request: WSGIRequest):
    """
    Alert the user that someone has admired their profile.
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=profile.user, device_notification__notification__code=NotificationCode.ADMIRED_USER).exists():
        device = user_device_notify(profile.user, 'Profile admired',
                           f"{request.user.first_name} has admired your profile",
                           request.user.getLink(), actions=[{'title': "View your profile",
                                                             'url': profile.getLink(),
                                                             'action': "action1"},
                                                            {'title': f"View {request.user.first_name}'s profile",
                                                             'url': request.user.getLink(),
                                                             'action': "action2"}])
    if EmailNotificationSubscriber.objects.filter(user=profile.user, email_notification__notification__code=NotificationCode.ADMIRED_USER).exists():
        email = sendActionEmail(
            to=profile.get_email, username=profile.getFName(), subject='Profile admired',
            header=f"{request.user.first_name} has admired your profile",
            actions=[{'text': "View your profile",
                      'url': profile.getLink()},
                     {'text': f"View {request.user.first_name}'s profile",
                      'url': request.user.getLink()}],
            footer=f"You can thank {request.user} and reach out to them.",
            conclusion=f"If you're being spammed by this mail or this is an error, please report to us."
        )
    return device, email