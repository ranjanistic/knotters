from django.core.handlers.wsgi import WSGIRequest
from main.methods import renderView, respondJson, respondRedirect
from main.strings import Code, Template, URL
from main.decorators import normal_profile_required, decode_JSON
from django.views.decorators.http import require_GET, require_POST
from django.http.response import HttpResponse
from ratelimit.decorators import ratelimit
from projects.models import Topic, BaseProject
from .models import *
from datetime import datetime, timedelta
from django.views.decorators.csrf import csrf_exempt
#from django.db.models import Q
from main.decorators import require_GET
from compete.models import Competition
from management.models import (CorePartner)

@csrf_exempt
@require_GET
def getallcourses(request: WSGIRequest):
    courselist = Course.objects.all()
    return respondJson(Code.OK, dict(
        courses=list(
            map(
                lambda course: dict(
                    id=course.id,
                    name=course.title,
                    short_desc=course.short_desc,
                    long_desc=course.long_desc,
                    picture=course.get_abs_dp,
                    total_lessons=course.total_lessons(),
                ), courselist
            )
        )
    ))



@csrf_exempt
@normal_profile_required
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
@require_GET
def getCoursebyID(request: WSGIRequest, courseID):
    course = Course.objects.get(id=courseID)
    return respondJson(Code.OK, dict(
        course=dict(
            id=course.id,
            name=course.title,
            short_desc=course.short_desc,
            long_desc=course.long_desc,
            total_lessons=course.total_lessons(),)
    ),)




@csrf_exempt
@normal_profile_required
@require_GET
def lessoninfo(request: WSGIRequest, lessonID):
    lesson = Lesson.objects.get(id=lessonID)
    return respondJson(Code.OK, dict(
        lesson=dict(
            id=lesson.id,
            name=lesson.name,
            type=lesson.type,
            course=lesson.course,
            data=lesson.data(),)
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def coursereview(request: WSGIRequest, review):
    course_review = CourseReview.objects.filter(course=review)
    return respondJson(Code.OK, dict(
        course_review=dict(
            id=course_review.id,
            coursename=course_review.course,
            _review=course_review.review,
            reviewer=course_review.givenby,
            rating=course_review.rating,
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def allreviews(request: WSGIRequest):
    reviews = CourseReview.objects.filter()
    return respondJson(Code.OK, dict(
        _reviews=list(
            map(
                lambda reviewlist: dict(
                    id=reviewlist.id,
                    coursename=reviewlist.course,
                    _review=reviewlist.review,
                    reviewer=reviewlist.givenby,
                    rating=reviewlist.rating,
                ), reviews
            )
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def deletereview(request: WSGIRequest, review):
    delete_review = CourseReview.objects.get(id=review)
    delete_review.delete()
    return respondJson(Code.OK, dict(
        delete_review=dict(
            id=delete_review.id,
            coursename=delete_review.course,
            _review=delete_review.review,
            reviewer=delete_review.givenby,
            rating=delete_review.rating,
        )
    ))


@csrf_exempt
@normal_profile_required
@require_POST
def removelessonhistory(request: WSGIRequest, lessonID):
    history = Lesson.objects.get(id=lessonID)
    history.delete()
    return respondJson(Code.OK, dict())

@csrf_exempt
@require_GET
def lessonlist(request: WSGIRequest, courseID):
    lesson = Lesson.objects.filter(course=courseID)
    return respondJson(Code.OK, dict(
        lessons=list(
            map(
                lambda lesson: dict(
                    id=lesson.id,
                    name=lesson.name,
                    type=lesson.type,
                    courseID=lesson.course.id,
                    data=lesson.data,
                )), lesson
        )
    ))


@csrf_exempt
@normal_profile_required
@require_POST
def addcoursereview(request,courseID):
    id=Course.object.get(id=courseID)
    course = request.POST['course']
    review = request.POST['review']
    givenby = request.user.profile
    rating = request.POST['rating']
    addreview = CourseReview.objects.create(
        id=id, course=course, review=review, givenby=givenby, rating=rating)
    return respondJson(Code.OK, dict(
        addreview=dict(
            addreview=dict(
                id=addreview.id,
                course=addreview.course,
                review=addreview.review,
                givenby=addreview.givenby,
                rating=addreview.rating,
            )
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def seehistory(request: WSGIRequest):
    history = CourseUserHistory.objects.filter(profile=request.user.profile)
    return respondJson(Code.OK, dict(
        history=dict(
            id=history.id,
            profile=history.profile,
            course=history.course,
            lesson=history.lesson,
        )
    ))


@csrf_exempt
@normal_profile_required
@require_POST
def add_to_history(request,lessonID):
    id = Lesson.objects.get(id=lessonID)
    profile = request.POST['profile']
    course = request.POST['course']
    lesson = request.POST['lesson']
    history = CourseUserHistory.objects.create(
        id=id, profile=profile, course=course, lesson=lesson)
    return respondJson(Code.OK, dict(
        history=dict(
            history=dict(
                id=history.id,
                profile=history.profile,
                course=history.course,
                lesson=history.lesson,
            )
        )
    ))


@csrf_exempt
@normal_profile_required
def enrollment(request: WSGIRequest, courseID):
    profile = request.user.profile
    course = Course.objects.get(id=courseID)
    enrollment = CourseUserEnrollment.objects.filter(course=course, profile=profile).first()
    if request.method == Code.POST:
        if not enrollment:
            enrollment = CourseUserEnrollment.objects.create(
                course=course,
                profile=profile,
                enrolledAt=timezone.now(),
                expireAt=timezone.now()+timedelta(seconds=10)
            )
        return respondJson(Code.OK, dict(
            enrollment=dict(
                id=enrollment.id,
                course=enrollment.course.id,
                enrolledAt=enrollment.enrolledAt,
                expireAt=enrollment.expireAt,
                isActive=enrollment.isActive(),
            )
        ))
    elif request.method == Code.GET:
        if enrollment:
            return respondJson(Code.OK, dict(
                enrollment=dict(
                    id=enrollment.id,
                    course=enrollment.course.id,
                    enrolledAt=enrollment.enrolledAt,
                    expireAt=enrollment.expireAt,
                    isActive=enrollment.isActive(),
                )
            ))
        else:
            return respondJson(Code.NO, dict(
                enrollment=False
            ), status=404)
