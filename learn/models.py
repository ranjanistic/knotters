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
    courseid:UUID=models.UUIDField(primary_key=True,default=uuid4)
    title=models.CharField(max_length=75)
    short_desc=models.CharField(max_length=250)
    long_desc=models.CharField(max_length=500)
    #lessons=models.ForeignKey(Lesson,on_delete=models.CASCADE)
    #raters = models.ManyToManyField(Profile, through="LessonUserRating", default=[], related_name='lesson_user_rating')
    lessonCount=models.IntegerField(default=0)
    #likes = models.ManyToManyField(Profile, through='CourseLikes', default=[], related_name='course_likes')
    creator = models.ForeignKey(Profile, related_name = "course", on_delete=models.CASCADE)

class Lesson(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4)
    name=models.CharField(max_length=75)
    #lessontype=models.ForeignKey(Course,on_delete=models.CASCADE)
    courseid=models.ForeignKey(Course,on_delete=models.CASCADE)

class rating(models.Model):
    rating=models.PositiveIntegerField(primary_key=True,default=0,blank=True)
    review_text=models.CharField(max_length=500)
    creator=models.ForeignKey(Profile,related_name="rating",on_delete=models.CASCADE)
    courseid=models.ForeignKey(Course,on_delete=models.CASCADE)

class profiletoken():
    id=Profile.id
    name=Profile.user
    is_active = Profile.is_active
    date_joined = Profile.createdOn
    USERNAME_FIELD = 'email'

class coursereview(models.Model):
    id:UUID=models.UUIDField(primary_key=True,default=uuid4)
    courseid=models.ForeignKey(Course,on_delete=models.CASCADE)
    review=models.CharField(max_length=500)
    givenby=models.ForeignKey(Profile,on_delete=models.CASCADE)
