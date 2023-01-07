from django.contrib import admin

from .models import *

admin.site.register(Report)
admin.site.register(Feedback)
admin.site.register(ReportCategory)
admin.site.register(ActivityRecord)
admin.site.register(HookRecord)
admin.site.register(GhMarketApp)
admin.site.register(GhMarketPlan)
admin.site.register(Management)
admin.site.register(ManagementPerson)
admin.site.register(APIKey)
admin.site.register(ManagementInvitation)
admin.site.register(ContactCategory)
admin.site.register(ContactRequest)
admin.site.register(ThirdPartyLicense)
admin.site.register(ThirdPartyAccount)
admin.site.register(Donor)
admin.site.register(CareerPosition)
admin.site.register(CareerApplication)
admin.site.register(CareerType)
