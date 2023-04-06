from django.core.handlers.wsgi import WSGIRequest
from main.methods import errorLog, renderView, respondJson, respondRedirect
from main.strings import Code, Message,setURLAlerts,Template,URL
from django.shortcuts import redirect
from django.utils import timezone
from howto.models import Article, ArticleTopic,ArticleTag
from .models import Course,Lesson
from main.decorators import require_JSON, normal_profile_required, decode_JSON
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http.response import Http404, HttpResponse,JsonResponse
from ratelimit.decorators import ratelimit
from django.core.cache import cache
from uuid import UUID
from projects.methods import addTagToDatabase, topicSearchList, tagSearchList
from django.conf import settings
from projects.models import Topic, Tag,BaseProject
from django.http import JsonResponse
from people.methods import addTopicToDatabase
from projects.methods import topicSearchList
from people.models import User
import jwt
from django.views.decorators.csrf import csrf_exempt
from django.db.models.query_utils import Q
from datetime import timedelta
from main.decorators import knotters_only, bearer_required, require_GET
from compete.models import Competition
from management.models import (CorePartner)

@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def logintoken(request: WSGIRequest):
    if request.user.is_authenticated:
        try:
            token = jwt.encode(dict(id=request.user.profile.get_userid, exp=timezone.now()+timedelta(days=7)), settings.SECRET_KEY, algorithm="HS256")
            return respondJson(Code.OK, data=dict(token=token))
        except KeyError as k:
            print(k)
            return respondJson(Code.NO, error=Message.INVALID_REQUEST, status=400)
        except ObjectDoesNotExist:
            return respondJson(Code.NO, error=Message.USER_NOT_EXIST, status=404)
        except Exception as e:
            errorLog(e)
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)
    else:
        return respondJson(Code.NO, error=Message.USER_NOT_EXIST, status=404)
    
@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def mytoken(request: WSGIRequest):
    try:
        prof=request.user.profile()
        return respondJson(Code.OK, data=dict(user=dict(
                   id=prof.get_userid, name=prof.get_name, email=prof.get_email,is_moderator=prof.is_moderator, is_mentor=prof.is_mentor, is_verified=prof.is_verified, is_manager=prof.is_manager(), nickname=prof.nickname, picture=prof.get_abs_dp)))
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED, status=500)
    
@normal_profile_required
@require_JSON
def topicsSearch(request: WSGIRequest, articleID: UUID) -> JsonResponse:
    try:
        query = str(request.POST['query'][:100]).strip()
        if not query:
            raise KeyError(query)
        limit = int(request.POST.get('limit', 3))
        article: Article = Article.objects.get(id=articleID, author=request.user.profile)
        cacheKey = f"article_topics_search_{query}"
        excluding = []
        if article:
            excluding = list(
                map(lambda topic: topic.id.hex, article.getTopics()))
            cacheKey = cacheKey + "".join(map(str, excluding))

        return respondJson(Code.OK, dict(
            topics=topicSearchList(query, excluding, limit, cacheKey)
        ))
    except (ObjectDoesNotExist, ValidationError, KeyError) as e:
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
    
@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def topicsUpdate(request: WSGIRequest, articleID: UUID) -> HttpResponse:
    json_body = request.POST.get("JSON_BODY", False)
    try:
        addtopicIDs = request.POST.get('addtopicIDs', None)
        removetopicIDs = request.POST.get('removetopicIDs', None)
        addtopics = request.POST.get('addtopics', None)

        article: Article = Article.objects.get(id=articleID, author=request.user.profile)

        if not (addtopicIDs or removetopicIDs or addtopics):
            if json_body:
                return respondJson(Code.NO, error=Message.NO_TOPICS_SELECTED)
            return redirect(article.getLink(error=Message.NO_TOPICS_SELECTED))

        if removetopicIDs:
            if not json_body:
                removetopicIDs = removetopicIDs.strip(',').split(',')
            ArticleTopic.objects.filter(
                article=article, topic__id__in=removetopicIDs).delete()

        if addtopicIDs:
            if not json_body:
                addtopicIDs = addtopicIDs.strip(',').split(',')
            if len(addtopicIDs) < 1:
                raise ObjectDoesNotExist(addtopicIDs, article)

            articletops = ArticleTopic.objects.filter(article=article)
            currentcount = articletops.count()
            if currentcount + len(addtopicIDs) > 3:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(article.getLink(error=Message.MAX_TOPICS_ACHEIVED))
            for topic in Topic.objects.filter(id__in=addtopicIDs):
                article.topics.add(topic)
                for tag in article.getTags():
                    topic.tags.add(tag)

        if addtopics and len(addtopics) > 0:
            count = ArticleTopic.objects.filter(article=article).count()
            if not json_body:
                addtopics = addtopics.strip(',').split(',')
            if count + len(addtopics) > 3:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(article.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            articletopics = []
            for top in addtopics:
                topic = addTopicToDatabase(
                    top, request.user.profile, article.getTags())
                articletopics.append(ArticleTopic(
                    topic=topic, article=article))

        if json_body:
            return respondJson(Code.OK, message=Message.TOPICS_UPDATED)
        return redirect(article.getLink(success=Message.TOPICS_UPDATED))
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)


@normal_profile_required
@require_JSON
def tagsSearch(request: WSGIRequest, articleID: UUID) -> JsonResponse:
    try:
        query = str(request.POST["query"][:100]).strip()
        if not query:
            raise KeyError(query)
        limit = int(request.POST.get("limit", 5))

        article: Article = Article.objects.get(id=articleID, author=request.user.profile)

        cacheKey = f"article_tag_search_{query}"
        excludeIDs = []
        if article:
            excludeIDs = list(map(lambda tag: tag.id.hex, article.getTags()))
            cacheKey = cacheKey + "".join(map(str, excludeIDs))
            
        return respondJson(Code.OK, dict(
            tags=tagSearchList(query, excludeIDs, limit, cacheKey)
        ))
    except (ObjectDoesNotExist, ValidationError, KeyError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def tagUpdate(request: WSGIRequest, articleID: UUID) -> HttpResponse:
    json_body = request.POST.get(Code.JSON_BODY, False)
    next = None
    article = None
    try:
        addtagIDs = request.POST.get('addtagIDs', None)
        addtags = request.POST.get('addtags', None)
        removetagIDs = request.POST.get('removetagIDs', None)

        article: Article = Article.objects.get(id=articleID, author=request.user.profile)

        next = request.POST.get('next', article.getLink())

        if not (addtagIDs or removetagIDs or addtags):
            return respondJson(Code.NO)

        if removetagIDs:
            if not json_body:
                removetagIDs = removetagIDs.strip(',').split(",")
            ArticleTag.objects.filter(
                article=article, tag__id__in=removetagIDs).delete()

        currentcount = ArticleTag.objects.filter(article=article).count()
        if addtagIDs:
            if not json_body:
                addtagIDs = addtagIDs.strip(',').split(",")
            if len(addtagIDs) < 1:
                if json_body:
                    return respondJson(Code.NO, error=Message.NO_TAGS_SELECTED)
                return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
            if currentcount + len(addtagIDs) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.MAX_TAGS_ACHEIVED))
            for tag in Tag.objects.filter(id__in=addtagIDs):
                article.tags.add(tag)
                for topic in article.getTopics():
                    topic.tags.add(tag)
            currentcount = currentcount + len(addtagIDs)

        if addtags:
            if not json_body:
                addtags = addtags.strip(',').split(",")
            if (currentcount + len(addtags)) <= 5:
                for tag in map(lambda addtag: addTagToDatabase(
                        addtag, request.user.profile), addtags):
                    article.tags.add(tag)
                    for topic in article.getTopics():
                        topic.tags.add(tag)
                currentcount = currentcount + len(addtags)
            else:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TAGS_ACHEIVED)
                return redirect(setURLAlerts(next, error=Message.MAX_TAGS_ACHEIVED))

        if json_body:
            return respondJson(Code.OK)
        return redirect(next)
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if next:
            return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO)
        if next:
            return redirect(setURLAlerts(next, error=Message.NO_TAGS_SELECTED))
        raise Http404(e)

@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    competition: Competition = Competition.latest_competition()
    if request.user.is_authenticated:
        if not request.user.profile.on_boarded:
            return respondRedirect(path=URL.ON_BOARDING)
        return renderView(request, Template.HOME, dict(competition=competition))

    topics = Topic.homepage_topics()
    project = BaseProject.homepage_project()
    partners = CorePartner.objects.filter(hidden=False)
    return renderView(request, Template.INDEX, dict(topics=topics, project=project, competition=competition, partners=partners))

@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))

def courseactions(request:WSGIRequest,courseID:UUID)->JsonResponse:
    profile=request.user.profile
    json_body=request.POST.get(Code.JSON_BODY)
    addcourse=request.POST.get('addcourse',None)
    removecourse=request.POST.get('removecourse',None)
    course:Course=Course.object.get(id=courseID,creator=profile)
    try:
        course1:Course=Course.objects.get(id='CourseID',creator=profile)
        if not (addcourse or removecourse or addtitles):
            if json_body:
                return respondJson(Code.NO, error=Message.NO_TOPICS_SELECTED)
            return redirect(course1.getLink(error=Message.NO_TOPICS_SELECTED))

        if removecourse:
            if not json_body:
                removecourse = removecourse.strip(',').split(',')
            #LessonTopic.objects.filter(lesson=course1, topic__id__in=removecourse).delete()

        if addcourse:
            if not json_body:
                addcourse = addcourse.strip(',').split(',')
            for topic in Topic.objects.filter(id__in=addcourse):
                course1.topics.add(topic)
                for tag in course1.getTags():
                    topic.tags.add(tag)

        if addtitles and len(addtitles) > 0:
            #count = LessonTopic.objects.filter(lesson=lesson).count()
            if not json_body:
                addtitles = addtitles.strip(',').split(',')
            #LessonTopics = []
            for top in addtitles:
                topic = addTopicToDatabase(top, request.user.profile, course1.getTags())
                #LessonTopics.append(ArticleTopic(topic=topic, lesson=course1))
        if json_body:
            return respondJson(Code.OK, message=Message.TOPICS_UPDATED)
        return redirect(course1.getLink(success=Message.TOPICS_UPDATED))
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)
    
def addcoursereview(request:WSGIRequest):
    profile=request.user.profile

def lessonactions(request:WSGIRequest,lessonID:UUID)->JsonResponse:
    profile=request.user.profile
    lesson:Lesson=Lesson.object.get(id=lessonID,creator=profile)

#class usertokenapi(APIView):
#    permission_classes = (AllowAny)
#    def post(self, request):
#        user = request.data
#        serializer = UserSerializer(data=user)
#        serializer.is_valid(raise_exception=True)
#        serializer.save()
#        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

#class UserRetrieveUpdateAPIView(RetrieveUpdateAPIView):
#    permission_classes = (User.IsAuthenticated,)
#    serializer_class = UserSerializer
#    def get(self, request, *args, **kwargs):
#        serializer = self.serializer_class(request.user)
#        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
#    def put(self, request, *args, **kwargs):
#        serializer_data = request.data.get('user', {})
#        serializer = UserSerializer(request.user, data=serializer_data, partial=True)
#        serializer.is_valid(raise_exception=True)
#        serializer.save()
#        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    
#def authenticate_user(request):
#    try:
#        email = request.data['email']
#        password = request.data['password']
#        user = User.objects.get(email=email, password=password)
#        if user:
#            try:
#                payload = jwt_payload_handler(user)
#                token = jwt.encode(payload, settings.SECRET_KEY)
#                user_details = {}
#                user_details['name'] = "%s %s" % (
#                    user.first_name, user.last_name)
#                user_details['token'] = token
#                user_logged_in.send(sender=user.__class__,request=request, user=user)
#                return JsonResponse(user_details, status=status.HTTP_200_OK)
#            except Exception as e:
#                raise e
#        else:
#            res = {
#                'error': 'can not authenticate with the given credentials or the account has been deactivated'}
#            return JsonResponse(res, status=status.HTTP_403_FORBIDDEN)
#    except KeyError:
#        res = {'error': 'please provide a email and a password'}
#        return JsonResponse(res)
