from django.contrib import admin
from learn.models import *

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(CourseReview)
admin.site.register(CourseUserLikes)
admin.site.register(CourseUserRating)
admin.site.register(UserHistory)
admin.site.register(CourseUserEnrollment)
admin.site.register(LessonList)