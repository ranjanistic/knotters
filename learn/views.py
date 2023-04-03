from django.core.handlers.wsgi import WSGIRequest
from main.methods import errorLog, renderView, respondJson, respondRedirect
from main.strings import Code, Message,setURLAlerts,Template,URL
from django.shortcuts import redirect
from django.utils import timezone
from howto.models import Article, ArticleTopic,ArticleTag,rendererstr,Lesson,LessonTopic
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
import jwt
from django.views.decorators.csrf import csrf_exempt
from django.db.models.query_utils import Q
#from django.db.models import Q
from datetime import timedelta
from main.decorators import knotters_only, bearer_required, require_GET
from compete.models import Competition
from management.models import (CorePartner)

@csrf_exempt
@knotters_only
@bearer_required
@require_GET
def logintoken(request: WSGIRequest):
    if WSGIRequest.user.is_authenticated:
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
    """To search for topics for an article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The id of the article
        request.POST.query (str): The query to search for

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and topics found, otherwise main.strings.Code.NO
    """
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
    """To update the topics of a article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The id of the article
        request.POST.addtopicIDs (str): CSV of topic IDs
        request.POST.removetopicIDs (str): CSV of topic IDs
        request.POST.addtopics (str,list): CSV of topic names, or list of topic names if json body

    Raises:
        Http404: If the article does not exist, or invalid request

    Returns:
        HttpResponseRedirect: The redirect to the article page with relevant message
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
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
    """To search for tags for a article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The id of the article
        request.POST.query (str): The query to search for

    Returns:
        JsonResponse: The json response with main.strings.Code.OK and tags found, otherwise main.strings.Code.NO
    """
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
    """To update the tags of a article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The id of the article
        request.POST.addtagIDs (str): CSV of tag IDs
        request.POST.removetagIDs (str): CSV of tag IDs
        request.POST.addtags (str,list): CSV of tag names, or list of topic names if json body

    Raises:
        Http404: If the article does not exist, or invalid request

    Returns:
        HttpResponseRedirect: The redirect to the article page with relevant message
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
    """
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
    
@ratelimit(key='user_or_ip', rate='2/s')
@decode_JSON
def browseSearch(request: WSGIRequest) -> HttpResponse:
    """To search for articles

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object

    Raises:
        Http404: If any error occurs

    Returns:
        HttpResponse: The text/html search view response with the search results context
        JsonResponse: The json response with main.strings.Code.OK and articles, or main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        query = request.GET.get('query', request.POST.get('query', ""))[:100].strip()
        if not query:
            raise KeyError(query)
        limit = request.GET.get('limit', request.POST.get('limit', 10))
        excludeauthorIDs = []
        cachekey = f'article_browse_search_{query}{request.LANGUAGE_CODE}'
        if request.user.is_authenticated:
            excludeauthorIDs = request.user.profile.blockedIDs()
            cachekey = f"{cachekey}{''.join(excludeauthorIDs)}"
        articles = cache.get(cachekey, [])

        if not len(articles):
            specials = ('tag:', 'topic:', 'author:')
            pquery = None
            dbquery = Q()
            invalidQuery = False
            if query.startswith(specials):
                def specquerieslist(q):
                    return [
                        Q(tags__name__iexact=q),
                        Q(topics__name__iexact=q),
                        Q(
                            Q(author__user__first_name__iexact=q) | Q(author__user__last_name__iexact=q) | Q(
                                author__user__email__iexact=q) | Q(author__nickname__iexact=q)
                        ),
                        Q()
                    ]
                commaparts = query.split(",")
                for cpart in commaparts:
                    if cpart.strip().lower().startswith(specials):
                        special, specialq = cpart.split(':')
                        dbquery = Q(dbquery, specquerieslist(specialq.strip())[
                            list(specials).index(f"{special.strip()}:")])
                    else:
                        pquery = cpart.strip()
                        break
            else:
                pquery = query
            if pquery and not invalidQuery:
                dbquery = Q(dbquery, Q(
                    Q(author__user__first_name__istartswith=pquery)
                    | Q(author__user__last_name__istartswith=pquery)
                    | Q(author__user__email__istartswith=pquery)
                    | Q(author__nickname__istartswith=pquery)
                    | Q(topics__name__iexact=pquery)
                    | Q(tags__name__iexact=pquery)
                    | Q(heading__iexact=pquery)
                    | Q(subheading__iexact=pquery)
                    | Q(nickname__iexact=pquery)
                    | Q(topics__name__istartswith=pquery)
                    | Q(tags__name__istartswith=pquery)
                    | Q(heading__icontains=pquery)
                    | Q(subheading__icontains=pquery)
                    | Q(nickname__icontains=pquery)
                ))
            if not invalidQuery:
                articles: Article = Article.objects.exclude(author__user__id__in=excludeauthorIDs).exclude(is_draft=True).filter(dbquery).distinct()[0:limit]

                if len(articles):
                    cache.set(cachekey, articles, settings.CACHE_SHORT)

        if json_body:
            return respondJson(Code.OK, dict(
                articles=list(map(lambda m: dict(
                    id=m.get_id,
                    heading=m.heading, subheading=m.subheading, nickname=m.get_nickname,
                    url=m.get_link, author=m.author.get_name
                ), articles)),
                query=query
            ))
        return rendererstr(request, Template.Howto.BROWSE_SEARCH, dict(articles=articles, query=query))
    except (KeyError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)

@require_GET
def index(request: WSGIRequest) -> HttpResponse:
    """To render the index page (home/root page)

    Methods: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: If user is logged in, but not on-boarded, redirect to onboarding.
        HttpResponse: The rendered text/html view with context.
            If logged in, renders dashboard (home.html), else renders index.html

    NOTE: The template index.html is used for both logged in and logged out users. (the about page)

        The template home.html is only used for logged in users (the feed/dashboard).

        But main.views.index & main.views.home render these two interchangably, i.e.,

            main.views.home -> main.view.index (301) if logged in, else index.html

            main.views.index -> home.html if logged in, else index.html

    """

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
def lessonupdate(request:WSGIRequest,courseID:UUID):
    profile=request.user.profile
    json_body = request.POST.get("JSON_BODY", False)
    addtitleIDs = request.POST.get('addtitleIDs', None)
    removetitleIDs = request.POST.get('removetitleIDs', None)
    addtitles = request.POST.get('addtitles', None)
    lesson: Lesson = Lesson.objects.get(id=courseID, author=request.user.profile)
    #getcourse=request.get.POST()
    try:
        lesson: Lesson = Lesson.objects.get(id=courseID, author=request.user.profile)
        if not (addtitleIDs or removetitleIDs or addtitles):
            if json_body:
                return respondJson(Code.NO, error=Message.NO_TOPICS_SELECTED)
            return redirect(lesson.getLink(error=Message.NO_TOPICS_SELECTED))

        if removetitleIDs:
            if not json_body:
                removetitleIDs = removetitleIDs.strip(',').split(',')
            LessonTopic.objects.filter(lesson=lesson, topic__id__in=removetitleIDs).delete()

        if addtitleIDs:
            if not json_body:
                addtitleIDs = addtitleIDs.strip(',').split(',')
            for topic in Topic.objects.filter(id__in=addtitleIDs):
                lesson.topics.add(topic)
                for tag in lesson.getTags():
                    topic.tags.add(tag)

        if addtitles and len(addtitles) > 0:
            #count = LessonTopic.objects.filter(lesson=lesson).count()
            if not json_body:
                addtitles = addtitles.strip(',').split(',')
            LessonTopics = []
            for top in addtitles:
                topic = addTopicToDatabase(top, request.user.profile, lesson.getTags())
                LessonTopics.append(ArticleTopic(topic=topic, lesson=lesson))
        if json_body:
            return respondJson(Code.OK, message=Message.TOPICS_UPDATED)
        return redirect(lesson.getLink(success=Message.TOPICS_UPDATED))
    except (ObjectDoesNotExist, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        raise Http404(e)
