from django.contrib import admin
from .models import *


admin.site.register(Report)
admin.site.register(Feedback)
admin.site.register(ReportCategory)
admin.site.register(ActivityRecord)
admin.site.register(HookRecord)