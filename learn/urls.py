from django.urls import path
from main.strings import URL
from learn.views import *
  

urlpatterns = [
    path('courses',getallcourses),
    path('courses/<str:courseID>',getCoursebyID),
    path('courses/<str:courseID>/lessons',lessonlist),
    path('courses/<str:courseID>/enroll',enrollment),
    path('lessons/<str:lessonID>',lessoninfo),
    path('courses/<str:review>/reviews',coursereview),
    path('courses/<str:courseID>/addreview',addcoursereview),
    path('courses/<str:review>/deletereview',deletereview),
    path('userhistory',seehistory),
    path('userhistory/add',add_to_history),
    path('userhistory/remove',removelessonhistory),
]
