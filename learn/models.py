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
    id:UUID=models.UUIDField(primary_key=True,default=uuid4,editable=False)
    title=models.CharField(max_length=75)
    short_desc=models.CharField(max_length=250)
    long_desc=models.CharField(max_length=500)
    raters = models.ManyToManyField(Profile, through="CourseUserRating", default=[], related_name='course_user_rating')
    likes = models.ManyToManyField(Profile, through='CourseUserLikes', default=[], related_name='course_likes')
    creator = models.ForeignKey(Profile, related_name = "course_creator", on_delete=models.CASCADE)

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
    id:UUID=models.UUIDField(primary_key=True,default=uuid4)
    name=models.CharField(max_length=75)
    type=models.CharField(choices=(('video','video'),('image','image'),('text','text'),('document','document')),max_length=10)
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    data=models.TextField(max_length=200)

class CourseReview(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4)
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    review=models.CharField(max_length=500)
    givenby=models.ForeignKey(Profile,on_delete=models.CASCADE)
    rating=models.PositiveIntegerField()

#courseuserenrollment model to be created
