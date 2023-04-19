from django.contrib import admin

from .models import *


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    autocomplete_fields = ['reporter']


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    autocomplete_fields = ['feedbacker']

admin.site.register(ReportCategory)
admin.site.register(ActivityRecord)
admin.site.register(HookRecord)
admin.site.register(GhMarketApp)
admin.site.register(GhMarketPlan)

@admin.register(Management)
class ManagementAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']


@admin.register(ManagementPerson)
class ManagementPersonAdmin(admin.ModelAdmin):
    autocomplete_fields = ['person']


@admin.register(ManagementInvitation)
class ManagementInvitationAdmin(admin.ModelAdmin):
    autocomplete_fields = ['sender', 'receiver']

admin.site.register(ContactCategory)
admin.site.register(ContactRequest)


admin.site.register(ThirdPartyLicense)
admin.site.register(ThirdPartyAccount)


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']


@admin.register(CareerPosition)
class CareerPositionAdmin(admin.ModelAdmin):
    autocomplete_fields = ['creator']

admin.site.register(CareerType)

@admin.register(CorePartner)
class CorePartnerAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']
