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
    To notify author that article has created article
    """
    device, email = False, False
    if DeviceNotificationSubscriber.objects.filter(user=article.author.user, device_notification__notification__code=NotificationCode.CREATED_ARTICLE).exists():
        device = user_device_notify(article.author.user, "Article Created",
                            f"Your article - {article.get_nickname} - has been created by {request.user.first_name}",
                            article.getLink(),
                            actions=[{
                                'title': 'View Article',
                                'url': article.get_link(),
                                'action': "action1"},
                                ])

    if EmailNotificationSubscriber.objects.filter(user=article.author.user, email_notification__notification__code=NotificationCode.CREATED_ARTICLE).exists():
        email = sendActionEmail(
            to=article.author.getEmail(),
            username=article.author.getFName(),
            subject=f"Article Created",
            header=f"This is to inform you that your article - {article.get_nickname} - has been created by {request.user.first_name}.",
            actions=[{
                'text': 'View article',
                'url': article.get_link()
            }],
            footer=f"You can thank and reach out to {request.user.first_name}.",
            conclusion=f"If this action is unfamiliar, then you may contact us."
        )
    return device, email