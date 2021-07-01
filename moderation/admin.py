from django.contrib import admin
from .forms import ModerationAdminForm
from .models import *


@admin.register(Moderation)
class moderationAdmin(admin.ModelAdmin):
    list_display = ["moderator","type", "resolved", "status"]
    list_filter = ["type","moderator","status","resolved"]
    form = ModerationAdminForm
    # def all_moderator(self,instance):
    #     obj = User.objects.filter(is_moderator=True)
    #     return obj
    # all_moderator.short_description = "Returns all moderators"


@admin.register(LocalStorage)
class storageAdmin(admin.ModelAdmin):
    list_display = ["key","value"]

