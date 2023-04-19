from django.urls import path
from main.strings import URL
from learn.views import *
  

urlpatterns = [
    path('courses',getallcourses),
    path('courses/<str:courseID>',getCoursebyID),
    path('courses/<str:courseID>/lessons',getLessonsByCourse),
    path('courses/<str:courseID>/enrollment',handleCourseEnrollment),
    path('courses/<str:courseID>/admire', toggleCourseAdmiration),
    path('courses/<str:courseID>/admirers', getCourseAdmirers),
    path('lessons/<str:lessonID>',getLessonById),
    path('courses/<str:courseID>/reviews',getReviewsByCourse),
    path('courses/<str:courseID>/reviews/add',addReviewByCourse),
    path('reviews/<str:reviewID>/delete',deleteReviewById),
    path('userhistory',getUserLessonHistory),
    path('userhistory/add',addLessonToUserHistory),
    path('userhistory/remove',removeLessonFromUserHistory),
]
