from main.mailers import sendActionEmail
from main.env import PUBNAME
from .models import Article
from main.constants import NotificationCode
from django.core.handlers.wsgi import WSGIRequest
from auth2.models import DeviceNotificationSubscriber,EmailNotificationSubscriber
from main.methods import user_device_notify

def articleAdmired(request: WSGIRequest, article: Article):
    """
    To notify author of article that someone has admired their article
    """
    device, email = False, False
    if(article.is_draft == True ):
        return device, email 
    if DeviceNotificationSubscriber.objects.filter(user=article.author.user, device_notification__notification__code=NotificationCode.ADMIRED_ARTICLE).exists():
        device = user_device_notify(article.author.user, "Article Admired",
                            f"Your article - {article.get_nickname} - has been admired by {request.user.first_name}",
                            article.getLink(),
                            actions=[{
                                'title': 'View Article',
                                'url': article.get_link(),
                                'action': "action1"},
                                ])

    if EmailNotificationSubscriber.objects.filter(user=article.author.user, email_notification__notification__code=NotificationCode.ADMIRED_ARTICLE).exists():
        email = sendActionEmail(
            to=article.author.getEmail(),
            username=article.author.getFName(),
            subject=f"Article Admired",
            header=f"This is to inform you that your article - {article.get_nickname} - has been admired by {request.user.first_name}.",
            actions=[{
                'text': 'View article',
                'url': article.get_link()
            }],
            footer=f"You can thank and reach out to {request.user.first_name}.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def articleCreated(request: WSGIRequest, article: Article):
    """
    To notify author that article has been created
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=article.author.user, device_notification__notification__code=NotificationCode.ARTICLE_CREATED).exists():
        device = user_device_notify(article.author.user, "Article Created",
                            f"You have successfully created an article.",
                            article.getLink(),
                            actions=[{
                                'title': 'View Article',
                                'url': article.get_link(),
                                'action': "action1"},
                                {
                                'title': 'Edit Article',
                                'url': article.getEditLink(),
                                'action': "action2"}
                                ])

    if EmailNotificationSubscriber.objects.filter(user=article.author.user, email_notification__notification__code=NotificationCode.ARTICLE_CREATED).exists():
        email = sendActionEmail(
            to=article.author.getEmail(),
            username=article.author.getFName(),
            subject=f"Article Created",
            header=f"This is to inform you that you have successfully created an article. Visit the following link and start adding content to your brand new article.",
            actions=[{
                'text': 'View article',
                'url': article.get_link()
            },
            {
                'text': 'Edit Article',
                'url': article.getEditLink()
            }],
            footer=f"You can also create more articles and keep contributing to the guides.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def articlePublished(request: WSGIRequest, article: Article):
    """
    To notify author of article that their article has been published successfully
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=article.author.user, device_notification__notification__code=NotificationCode. ARTICLE_PUBLISHED).exists():
        device = user_device_notify(article.author.user, "Article Published",
                            f"Your article - {article.get_nickname} - has been successfully published.",
                            article.getLink(),
                            actions=[{
                                'title': 'View Article',
                                'url': article.get_link(),
                                'action': "action1"},
                                ])

    if EmailNotificationSubscriber.objects.filter(user=article.author.user, email_notification__notification__code=NotificationCode.ARTICLE_PUBLISHED).exists():
        email = sendActionEmail(
            to=article.author.getEmail(),
            username=article.author.getFName(),
            subject=f"Article Published",
            header=f"This is to inform you that your article - {article.get_nickname} - has been successfully published.",
            actions=[{
                'text': 'View article',
                'url': article.get_link()
            }],
            footer=f"The article can now only be edited for a period of 7 days, after that you won't be able to make any changes. So, hurry and make those last minute(or week ;D) changes.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email


def articleDeleted(request: WSGIRequest, article: Article):
    """
    To notify author of article that their article has been deleted successfully
    """
    device, email = False, False
    if(article.is_draft == True ):
        return device, email 
    if DeviceNotificationSubscriber.objects.filter(user=article.author.user, device_notification__notification__code=NotificationCode. ARTICLE_DELETED).exists():
        device = user_device_notify(article.author.user, "Article Deleted",
                            f"Your article - {article.get_nickname} - has been successfully deleted."
                            )

    if EmailNotificationSubscriber.objects.filter(user=article.author.user, email_notification__notification__code=NotificationCode.ARTICLE_DELETED).exists():
        email = sendActionEmail(
            to=article.author.getEmail(),
            username=article.author.getFName(),
            subject=f"Article Deleted",
            header=f"This is to inform you that your article - {article.get_nickname} - has been successfully deleted.",
            footer=f"You can create more articles anytime.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email