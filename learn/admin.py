from django.contrib import admin
from learn.models import *


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    autocomplete_fields = ['creator']


admin.site.register(Lesson)


@admin.register(CourseUserReview)
class CourseReviewAdmin(admin.ModelAdmin):
    autocomplete_fields = ['creator']


admin.site.register(CourseUserLikes)


@admin.register(UserLessonHistory)
class UserLessonHistoryAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']


@admin.register(UserCourseEnrollment)
class UserCourseEnrollmentAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']


@admin.register(EnrollmentCouponCode)
class EnrollmentCouponCodeAdmin(admin.ModelAdmin):
    autocomplete_fields = ['creator']


@admin.register(UserCoursePayment)
class UserCoursePaymentAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']


@admin.register(CourseTag)
class CourseTagAdmin(admin.ModelAdmin):
    autocomplete_fields = ['tag']


@admin.register(CourseTopic)
class CourseTopicAdmin(admin.ModelAdmin):
    autocomplete_fields = ['topic']