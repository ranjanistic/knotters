from django.contrib import admin
from .forms import ModerationAdminForm
from .models import *


@admin.register(Moderation)
class moderationAdmin(admin.ModelAdmin):
    list_display = ["moderator","__str__","type", "resolved", "status", "requestOn","respondOn"]
    list_filter = ["type","status","resolved"]
    ordering = ["requestOn","respondOn"]
    form = ModerationAdminForm
    # def all_moderator(self,instance):
    #     obj = User.objects.filter(is_moderator=True)
    #     return obj
    # all_moderator.short_description = "Returns all moderators"


@admin.register(LocalStorage)
class storageAdmin(admin.ModelAdmin):
    list_display = ["key","value"]


admin.site.register(ReportedModeration)