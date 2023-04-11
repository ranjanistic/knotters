#from rest_framework import serializers
#from.models import *
#from people.models import User
#
#class UserSerializer(models.Model):#serializers.ModelSerializer:
#    #date_joined = serializers.ReadOnlyField()
#    class Meta(object):
#        model = User
#        fields = ('id', 'email', 'first_name', 'last_name','date_joined', 'password')
#        extra_kwargs = {'password': {'write_only': True}}
#
#class CourseSerializer(models.Model):
#    class Meta(object):
#       model=Course
#       fields=('courseID','title','short_desc','long_desc','lessons','raters','lessonCount','likes','creator')
#       extra_kwargs={}
#
#class LessonSerializer(models.Model):
#    class Meta(object):
#        model=Lesson
#        fields=('id','name','lessontype','course')
#        extra_kwargs={}
#
#class RatingSerializer(models.Model):
#    class Meta(object):
#        model=rating
#        fields=('rating','review','creator','courseID')
#        extra_kwargs={}