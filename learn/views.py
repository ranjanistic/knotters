from django.core.handlers.wsgi import WSGIRequest
from main.methods import respondJson
from main.strings import Code
from main.decorators import normal_profile_required
from django.views.decorators.http import require_GET, require_POST
from .models import *
from django.views.decorators.csrf import csrf_exempt
from main.decorators import require_GET



@csrf_exempt
@require_GET
def getallcourses(request: WSGIRequest):
    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 10))
    lfrom = (page-1)*size
    lto = lfrom + size
    courses = Course.objects.filter(draft=False, trashed=False)[lfrom:lto]
    return respondJson(Code.OK, dict(
        courses=list(
            map(
                lambda course: dict(
                    id=course.get_id,
                    name=course.title,
                    short_desc=course.short_desc,
                    long_desc=course.long_desc,
                    picture=course.get_abs_dp,
                    creator=course.creator.get_dict(),
                    total_lessons=course.total_lessons(),
                    rating=course.get_avg_rating(),
                    topics=course.get_topics_dict(),
                    total_admirers=course.total_admirers()
                ), courses
            )
        )
    ))


@csrf_exempt
@require_GET
def getCoursebyID(request: WSGIRequest, courseID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    course = Course.objects.filter(
        id=courseID, draft=False, trashed=False).first()
    if not course:
        return respondJson(Code.NO, error='Course not found', status=404)
    return respondJson(Code.OK, dict(
        course=dict(
            id=course.get_id,
            name=course.title,
            short_desc=course.short_desc,
            long_desc=course.long_desc,
            picture=course.get_abs_dp,
            creator=course.creator.get_dict(),
            total_lessons=course.total_lessons(),
            rating=course.get_avg_rating(),
            topics=course.get_topics_dict(),
            tags=course.get_tags_dict()
        )
    ))


@csrf_exempt
@require_GET
def getLessonsByCourse(request: WSGIRequest, courseID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    course = Course.objects.filter(
        id=courseID, draft=False, trashed=False).first()
    if not course:
        return respondJson(Code.NO, error='Course not found', status=404)
    lessons = Lesson.objects.filter(course=course, trashed=False)
    return respondJson(Code.OK, dict(
        lessons=list(
            map(
                lambda lesson: dict(
                    id=lesson.get_id,
                    name=lesson.name,
                    type=lesson.type,
                    courseId=lesson.course.get_id,
                ), lessons),
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def getLessonById(request: WSGIRequest, lessonID):
    try:
        UUID(lessonID)
    except:
        return respondJson(Code.NO, status=400)
    lesson = Lesson.objects.filter(id=lessonID, trashed=False).first()
    if not lesson or lesson.is_draft() or lesson.is_trashed():
        return respondJson(Code.NO, error='Lesson not found', status=404)
    if not UserCourseEnrollment.get_profile_course_valid_enrollement(request.user.profile, lesson.course):
        return respondJson(Code.NO, error='Enrollment not active', status=403)
    return respondJson(Code.OK, dict(
        lesson=dict(
            id=lesson.get_id,
            name=lesson.name,
            type=lesson.type,
            course=lesson.course,
            data=lesson.data,
        )
    ))


@csrf_exempt
@require_GET
def getReviewsByCourse(request: WSGIRequest, courseID: UUID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    course = Course.objects.filter(
        id=courseID, draft=False, trashed=False).first()
    if not course:
        return respondJson(Code.NO, error='Course not found', status=404)
    reviews = CourseUserReview.objects.filter(
        course=course, draft=False, trashed=False, suspended=False)
    return respondJson(Code.OK, dict(
        reviews=list(
            map(
                lambda review: dict(
                    id=review.id,
                    courseId=review.course.id,
                    review=review.review,
                    reviewer=review.creator.get_dict(),
                    score=review.score,
                    canBeDeleted=(
                        request.user.is_authenticated and review.creator == request.user.profile)
                ), reviews
            )
        )
    ))


@csrf_exempt
@normal_profile_required
@require_POST
def addReviewByCourse(request, courseID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    course = Course.object.filter(id=courseID).first()
    if not course:
        return respondJson(Code.NO, error='Course not found', status=404)
    review = request.POST.get('review','')
    score = int(request.POST.get('score', 1))
    review = CourseUserReview.objects.create(
        course=course, review=review,draft=False, creator=request.user.profile, score=score)
    return respondJson(Code.OK, dict(
        review=dict(
            id=review.id,
            courseId=review.course.get_id,
            review=review.review,
            reviewer=review.creator.get_dict(),
            score=review.score,
            canBeDeleted=True
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def deleteReviewById(request: WSGIRequest, reviewID):
    try:
        UUID(reviewID)
    except:
        return respondJson(Code.NO, status=400)
    deleted = CourseUserReview.objects.filter(
        id=reviewID, creator=request.user.profile).delete()
    if not deleted:
        return respondJson(Code.NO, error='Review not found', status=404)
    return respondJson(Code.OK)


@csrf_exempt
@normal_profile_required
@require_POST
def addLessonToUserHistory(request: WSGIRequest, lessonID):
    try:
        UUID(lessonID)
    except:
        return respondJson(Code.NO, status=400)
    lesson = Lesson.objects.filter(id=lessonID).first()
    if not lesson:
        return respondJson(Code.NO, error='Lesson not found', status=404)
    if not UserCourseEnrollment.get_profile_course_valid_enrollement(request.user.profile,lesson.course):
        return respondJson(Code.NO, error='Enrollment not active', status=403)
    history: UserLessonHistory = UserLessonHistory.objects.get_or_create(
        profile=request.user.profile, lesson=lesson)
    return respondJson(Code.OK, dict(
        history=dict(
            id=history.id,
            courseId=history.course().id,
            lesson=history.lesson.get_dict(),
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def getUserLessonHistory(request: WSGIRequest):
    histories = UserLessonHistory.objects.filter(profile=request.user.profile)
    return respondJson(Code.OK, dict(
        histories=list(
            map(
                lambda history: dict(
                    id=history.id,
                    courseId=history.course().id,
                    lesson=history.lesson.get_dict(),
                ), histories
            )
        )
    ))


@csrf_exempt
@normal_profile_required
@require_GET
def removeLessonFromUserHistory(request: WSGIRequest, lessonID):
    try:
        UUID(lessonID)
    except:
        return respondJson(Code.NO, status=400)
    lesson = Lesson.objects.filter(id=lessonID).first()
    if not lesson:
        return respondJson(Code.NO, error='Lesson not found', status=404)
    UserLessonHistory.objects.filter(
        profile=request.user.profile, lesson=lesson).delete()
    return respondJson(Code.OK)


@csrf_exempt
@normal_profile_required
def handleCourseEnrollment(request: WSGIRequest, courseID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    profile = request.user.profile
    course = Course.objects.get(id=courseID)

    enrollment: UserCourseEnrollment = UserCourseEnrollment.get_profile_course_valid_enrollement(
        profile, course)
    if request.method == Code.POST:
        coupon = request.POST.get('coupon', '').strip()
        payment = None
        if coupon:
            coupon = EnrollmentCouponCode.objects.filter(
                coupon=coupon, expireAt__gt=timezone.now(), valid_till__gt=timezone.now()).first()
            if not coupon:
                return respondJson(Code.NO, error="Invalid coupon code", status=400)
        else:
            payment = UserCoursePayment.objects.filter(
                profile=request.user.profile, course=course, expireAt__gt=timezone.now()).first()
            if not payment or not payment.is_successful():
                return respondJson(Code.NO, error="Payment not recieved, or is still pending.", status=400)
        if enrollment:
            expireAt = enrollment.expireAt
            isActive = enrollment.isActive()
            if coupon and coupon.expireAt > enrollment.expireAt:
                expireAt = coupon.expireAt
                isActive = coupon.isActive()
                UserCourseEnrollment.objects.filter(
                    id=enrollment.id
                ).update(payment=None, expireAt=expireAt)
            elif payment and payment.expireAt > enrollment.expireAt:
                expireAt = payment.expireAt
                isActive = payment.isActive()
                UserCourseEnrollment.objects.filter(
                    id=enrollment.id
                ).update(coupon=None, expireAt=expireAt)
            return respondJson(Code.OK, dict(
                enrollment=dict(
                    id=enrollment.id,
                    courseId=enrollment.course.id,
                    enrolledAt=enrollment.enrolledAt,
                    expireAt=expireAt,
                    isActive=isActive
                )
            ))
        else:
            if coupon and coupon.isActive():
                enrollment = UserCourseEnrollment.objects.create(
                    course=course,
                    profile=profile,
                    enrolledAt=timezone.now(),
                    expireAt=coupon.expireAt,
                    coupon=coupon,
                    payment=None
                )
            elif payment and payment.isActive():
                enrollment = UserCourseEnrollment.objects.create(
                    course=course,
                    profile=profile,
                    enrolledAt=timezone.now(),
                    expireAt=payment.expireAt,
                    payment=payment,
                    coupon=None
                )
            else:
                return respondJson(Code.NO, error='Invalid enrollment request.', status=400)
            return respondJson(Code.OK, dict(
                enrollment=dict(
                    id=enrollment.id,
                    courseId=enrollment.course.id,
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
                    courseId=enrollment.course.id,
                    enrolledAt=enrollment.enrolledAt,
                    expireAt=enrollment.expireAt,
                    isActive=enrollment.isActive(),
                )
            ))
        else:
            return respondJson(Code.NO, error="Enrollment not valid", status=404)


@csrf_exempt
@normal_profile_required
@require_GET
def toggleCourseAdmiration(request, courseID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    course = Course.objects.filter(
        id=courseID, trashed=False, draft=False).first()
    if not course:
        return respondJson(Code.NO, error='Course not found', status=404)
    CourseUserLikes.objects.get_or_create(
        course=course, profile=request.user.profile)
    return respondJson(Code.OK)


@csrf_exempt
@require_GET
def getCourseAdmirers(request, courseID):
    try:
        UUID(courseID)
    except:
        return respondJson(Code.NO, status=400)
    course = Course.objects.filter(
        id=courseID, trashed=False, draft=False).first()
    if not course:
        return respondJson(Code.NO, error='Course not found', status=404)
    page = int(request.GET.get('page', 1))
    size = int(request.GET.get('size', 10))
    lfrom = (page-1)*size
    lto = lfrom + size
    likes = CourseUserLikes.objects.filter(course=course)[lfrom:lto]
    admirers = list(map(lambda like: like.profile, likes))
    return respondJson(Code.OK, dict(admirers=admirers))
