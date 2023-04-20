from uuid import UUID, uuid4
from djongo import models
from main.methods import filterNickname
from time import time
from datetime import datetime
from django.utils import timezone
from people.models import Profile, Topic
from projects.models import Tag
from people.models import Profile
from .apps import APPNAME
from django.conf import settings
from main.strings import url
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
import math
from django.core.files.base import File
from random import randint


def courseImagePath(instance: "Profile", filename: str) -> str:
    fileparts = filename.split('.')
    return f"{APPNAME}/{str(instance.id)}_{str(uuid4().hex)}.{fileparts[-1]}"


def defaultImagePath() -> str:
    return f"{APPNAME}/default.png"


class Course(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    title = models.CharField(max_length=75)
    short_desc = models.CharField(max_length=250)
    long_desc = models.CharField(max_length=500)
    picture: File = models.ImageField(
        upload_to=courseImagePath, default=defaultImagePath)
    # tag= models.ArrayField(models.CharField(max_length=10), default=[])
    topics = models.ManyToManyField(
        Topic, through='CourseTopic', default=[], related_name='course_topics')
    tags = models.ManyToManyField(
        Tag, through='CourseTag', default=[], related_name='course_tags')
    raters = models.ManyToManyField(Profile, through="CourseUserReview", default=[
    ], related_name='course_user_review')
    admirers = models.ManyToManyField(
        Profile, through='CourseUserLikes', default=[], related_name='course_likes')
    creator = models.ForeignKey(
        Profile, related_name="course_creator", on_delete=models.CASCADE)
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    draft: bool = models.BooleanField(default=True)
    trashed: bool = models.BooleanField(default=False)
    cost = models.FloatField(default=0)
    cost_org = models.FloatField(default=0)

    def __str__(self):
        return self.title

    @property
    def get_id(self):
        return self.id.hex
        
    def total_lessons(self):
        return Lesson.objects.filter(course=self).count()

    def isRemoteDp(self) -> bool:
        """Checks if the user has a third party dp"""
        return str(self.picture).startswith("http") and not str(self.picture).startswith(settings.SITE)

    @property
    def get_dp(self) -> str:
        """Returns the user's dp URL"""
        dp = str(self.picture)
        return dp if self.isRemoteDp() else f"{settings.MEDIA_URL}{dp}" if not dp.startswith('/') else f"{settings.MEDIA_URL}{dp.removeprefix('/')}"

    @property
    def get_abs_dp(self) -> str:
        """Returns the user's dp absolute URL"""
        if self.get_dp.startswith('http:'):
            return self.get_dp
        return f"{settings.SITE}{self.get_dp}"

    def get_avg_rating(self):
        avgrating = 0
        if not avgrating:
            rating_list=CourseUserReview.objects.filter(course=self)
            num_of_ratings=len(rating_list)
            if (num_of_ratings==0):
                return 0.0
            total_sum=0
            for rating in rating_list:
                total_sum += rating.score
            avgrating = round(total_sum/(2*num_of_ratings),1)
        return avgrating

    def get_topics_dict(self):
        return list(map(lambda topic: dict(id=topic.id.hex, name=topic.name), self.topics.all()))
    def get_tags_dict(self):
        return list(map(lambda tag: dict(id=tag.id.hex, name=tag.name), self.tags.all()))
        
    def total_admirers(self):
        return self.admirers.count()



class CourseTag(models.Model):
    """Model for relation between a tag and an course"""
    class Meta:
        unique_together = ('tag', 'course')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    tag: Tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name='course_tag')
    """tag (ForeignKey<Tag>): tag related to the course"""
    course: Course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='tag_course')
    """course (ForeignKey<Course>): course related to tag"""


class CourseTopic(models.Model):
    """Model for relation between an admirer and an course"""
    class Meta:
        unique_together = ('topic', 'course')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    topic: Topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='course_topic')
    """topic (ForeignKey<Topic>): topic related to the course"""
    course: Course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='topic_course')
    """course (ForeignKey<Course>): course related to topic"""

class CourseUserLikes(models.Model):
    class Meta:
        unique_together = ('profile', 'course')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='course_like_profile')
    """profile (ForeignKey<Profile>): profile who rated the course"""
    course: Course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='liked_course')
    """course (ForeignKey<Course>): course which was rated"""


class Lesson(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=200)
    type = models.CharField(choices=(('video', 'video'), ('image', 'image'), ('text', 'text'), (
        'document', 'document'), ('game', 'game'), ('code', 'code')), max_length=10)
    course: Course = models.ForeignKey(Course, on_delete=models.CASCADE)
    data = models.TextField(max_length=200)
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    trashed: bool = models.BooleanField(default=False)

    @property
    def get_id(self):
        return self.id.hex
        
    def is_draft(self):
        return self.course.draft

    def is_trashed(self):
        return self.trashed or self.course.trashed

    def get_dict(self) -> dict:
        return dict(
            id=self.get_id,
            name=self.name,
            type=self.type,
            courseId=self.course.id,
        )


class CourseUserReview(models.Model):
    id: UUID = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    review = models.CharField(max_length=500, null=True, blank=True)
    creator: Profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(5)])
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    trashed = models.BooleanField(default=False)
    draft = models.BooleanField(default=True)
    suspended = models.BooleanField(default=False)


class EnrollmentCouponCode(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE)
    coupon = models.CharField(max_length=100)
    expireAt = models.DateTimeField(auto_now=False, default=timezone.now)
    valid_till = models.DateTimeField(auto_now=False, default=timezone.now)

    def __str__(self) -> str:
        return self.coupon

    def isActive(self):
        return self.expireAt > timezone.now()

    def isValid(self):
        return self.valid_till > timezone.now()

class UserCoursePayment(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='payment_user_profile')
    amount = models.FloatField(default=0)
    currency = models.CharField(choices=(('INR','INR'),), default='INR', max_length=10)
    status = models.CharField(choices=(
        ('pending', 'pending'), ('success', 'success'), ('failure', 'failure')), max_length=50)
    createdAt = models.DateTimeField(auto_now=False, default=timezone.now)
    completedAt = models.DateTimeField(auto_now=False, default=timezone.now, null=True, blank=True)
    expireAt = models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)

    def isActive(self):
        return self.is_successful() and self.expireAt > timezone.now()

    def is_successful(self):
        return self.status == 'success'

    def is_failure(self):
        return self.status == 'failure'

    def is_pending(self):
        return not self.is_successful() and not self.is_failure()


class UserCourseEnrollment(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='enrolled_user_profile')
    enrolledAt = models.DateTimeField(auto_now=False, default=timezone.now)
    expireAt = models.DateTimeField(auto_now=False, default=timezone.now)
    coupon: EnrollmentCouponCode = models.ForeignKey(
        EnrollmentCouponCode, on_delete=models.SET_NULL, null=True, blank=True)
    payment: UserCoursePayment = models.ForeignKey(
        UserCoursePayment, on_delete=models.SET_NULL, null=True, blank=True)
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)

    class Meta:
        unique_together = ('profile', 'course')

    def get_profile_course_valid_enrollement(profile: Profile, course: Course):
        enr: UserCourseEnrollment = UserCourseEnrollment.objects.filter(
            profile=profile, course=course).first()
        if not enr:
            enr: UserCourseEnrollment = UserCourseEnrollment.objects.filter(
                profile__in=profile.managements(True), course=course).first()

        if not enr or not enr.isActive():
            return None
        return enr

    def isActive(self):
        if self.coupon and self.coupon.isActive():
            return True
        if self.payment and self.payment.isActive():
            return True
        return self.expireAt > timezone.now()


class UserLessonHistory(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    createdOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)
    modifiedOn: datetime = models.DateTimeField(
        auto_now=False, default=timezone.now)

    def course(self):
        return self.lesson.course
