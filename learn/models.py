from uuid import UUID,uuid4
from djongo import models
from main.methods import filterNickname
from time import time
from datetime import datetime
from django.utils import timezone
from people.models import Profile,Topic
from projects.models import Tag
from people.models import Profile
from howto.apps import APPNAME
from django.conf import settings
from main.strings import url
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,BaseUserManager
import math

class Course(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4,editable=True)
    title=models.CharField(max_length=75)
    short_desc=models.CharField(max_length=250)
    long_desc=models.CharField(max_length=500)
    topics = models.ManyToManyField(Topic, through='CourseTopic', default=[], related_name='course_topics')
    tags = models.ManyToManyField(Tag, through='CourseTag', default=[], related_name='course_tags')
    raters = models.ManyToManyField(Profile, through="CourseUserRating", default=[], related_name='course_user_rating')
    admirers = models.ManyToManyField(Profile, through='CourseUserLikes', default=[], related_name='course_likes')
    creator = models.ForeignKey(Profile, related_name = "course_creator", on_delete=models.CASCADE)
    createdOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)

class CourseTag(models.Model):
    """Model for relation between a tag and an course"""
    class Meta:
        unique_together = ('tag', 'course')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    tag: Tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name='course_tag')
    """tag (ForeignKey<Tag>): tag related to the course"""
    course:Course  = models.ForeignKey(
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
    course:Course  = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='topic_course')
    """course (ForeignKey<Course>): course related to topic"""

class CourseUserRating(models.Model):
    class Meta:
        unique_together = ('profile', 'course')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='course_rater_profile')
    """profile (ForeignKey<Profile>): profile who rated the course"""
    course: Course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='rated_course')
    """course (ForeignKey<Course>): course which was rated"""
    score: float = models.FloatField(default=0, validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    text=models.TextField(max_length=150)


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
    id:UUID=models.UUIDField(primary_key=True,default=uuid4,editable=False)
    name=models.CharField(max_length=200)
    type=models.CharField(choices=(('video','video'),('image','image'),('text','text'),('document','document'),('game','game'),('code','code')),max_length=10)
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    data=models.TextField(max_length=200)
    createdOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)


class CourseReview(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4,editable=True)
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    review=models.CharField(max_length=500)
    creator=models.ForeignKey(Profile,on_delete=models.CASCADE)
    rating=models.PositiveIntegerField(default=0)
    createdOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)


class CourseUserEnrollment(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4,editable=False)
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    profile=models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='enrolled_user_profile')
    enrolledAt=models.DateTimeField(auto_now=False,default=timezone.now)
    expireAt= models.DateTimeField(auto_now=False, default=timezone.now)
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)

    class Meta:
        unique_together = ('profile','course')

    def isActive(self):
        return self.expireAt>timezone.now()
        

class CourseUserHistory(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4,editable=False)
    profile=models.ForeignKey(Profile, on_delete=models.CASCADE)
    lesson=models.ForeignKey(Lesson,on_delete=models.CASCADE)
    createdOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the course was created"""
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)