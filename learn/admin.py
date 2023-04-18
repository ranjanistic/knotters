from django.contrib import admin
from learn.models import *

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ['creator']

admin.site.register(Lesson)
admin.site.register(CourseReview)
admin.site.register(CourseUserLikes)
admin.site.register(CourseUserRating)
admin.site.register(CourseUserHistory)
admin.site.register(CourseUserEnrollment)