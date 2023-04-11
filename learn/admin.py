from django.contrib import admin
from learn.models import *

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(CourseReview)
admin.site.register(CourseUserLikes)
admin.site.register(CourseUserRating)