from django.urls import path
from main.strings import URL
from learn.views import *
  

urlpatterns = [
    path(URL.INDEX, index),
    path('courses',getallcourses),
    path('course/<str:courseID>',getCoursebyID),
    path('lesson/<str:lessonID>',lessoninfo),
    path('review/<str:review>',coursereview),
    path('reviews',allreviews),
    path('deletereview/<str:review>',deletereview),
    path('deletelessonhistory/<str:lesson>',removelessonhistory),
    path('lessonslist/<str:listlessons>',lessonlist),
    path('userhistory/<str:addrecord>',seehistory),
    path('userhistory/<str:id>',add_to_history),
    path('<str:courseID>/addreview',addcoursereview),
    path('course/<str:status>/enroll',enrollstatus),
    path('course/<str:courseid>/enroll',course_enroll),
]
