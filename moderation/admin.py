from django.contrib import admin
from people.models import User
from .models import *


@admin.register(moderation)
class moderationAdmin(admin.ModelAdmin):
    list_display = ["project","moderator","type"]
    list_filter = ["type","moderator"]

    # def all_moderator(self,instance):
    #     obj = User.objects.filter(is_moderator=True)
    #     return obj
    # all_moderator.short_description = "Returns all moderators"


@admin.register(localStorage)
class storageAdmin(admin.ModelAdmin):
    list_display = ["key","value"]

