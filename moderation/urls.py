from django.urls import path
from main.strings import url
from .views import moderation, message, action, reapply

urlpatterns = [
    path(url.Moderation.MODID, moderation),
    path(url.Moderation.MESSAGE, message),
    path(url.Moderation.ACTION, action),
    path(url.Moderation.REAPPLY, reapply),
]
