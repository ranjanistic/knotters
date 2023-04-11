from django.urls import path
from main.strings import URL
from learn.views import *
  

urlpatterns = [
    path(URL.INDEX, index),
    path('courses/',getallcourses),
    path('course/<str:courseID>',getCoursebyID),
    path('lesson/<str:lessonID>',lessoninfo),
    path('review/<str:review>',coursereview),
    path('lessonslist/<str:listlessons>',lessonlist),
    path('userhistory/<str:addrecord>',recordhistory),
    path('deletereview/<str:review>',deletereview),
    path('deletelesson/<str:lesson>',removelessonhistory),
]
