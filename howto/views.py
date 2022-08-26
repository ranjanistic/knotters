from django.shortcuts import redirect 
from howto.models import Article, Section, ArticleTopic, ArticleTag
from howto.methods import renderer, articleRenderData
from main.strings import Template, Code , Message, URL, Action, setURLAlerts
from main.methods import respondJson, errorLog, respondRedirect, base64ToFile, base64ToImageFile
from main.decorators import require_JSON, normal_profile_required, decode_JSON
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http.response import Http404, HttpResponse
from ratelimit.decorators import ratelimit
from uuid import UUID
from django.conf import settings
from django.core.cache import cache
from projects.models import Topic, Tag
from django.core.handlers.wsgi import WSGIRequest
from django.http import JsonResponse
from django.db.models.query_utils import Q
from people.methods import addTopicToDatabase
from projects.methods import addTagToDatabase
from .apps import APPNAME


def index(request):
    articles=Article.objects.filter(is_draft=False)
    return renderer(request, Template.Howto.INDEX, dict(articles=articles))


@normal_profile_required
@require_GET
def createArticle(request: WSGIRequest):
    """To render create article page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    try:
        if Article.canCreateArticle(request.user.profile):
            return renderer(request, Template.Howto.CREATE)
        raise ValidationError(request.user.profile)
    except ValidationError as e:
        raise Http404("Unauthorised access", e)
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
def saveArticle(request: WSGIRequest):
    """To save an article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the article page if created successfully, else to the create page.
    """
    articleobj = None
    alerted = False
    try:
        # acceptedTerms: bool = request.POST.get("acceptterms", False)
        # if not acceptedTerms:
        #     return respondRedirect(APPNAME, URL.Howto.CREATE, error=Message.TERMS_UNACCEPTED)
        heading = str(request.POST["heading"]).strip()
        subheading = str(request.POST["subheading"]).strip()
        
        articleobj = Article.objects.create(heading=heading, subheading=subheading, author=request.user.profile)
        if not articleobj:
            raise Exception(articleobj)
        alerted = True
        return redirect(articleobj.getLink(success=Message.ARTICLE_CREATED))
    except KeyError:
        if articleobj and not alerted:
            articleobj.delete()
        return respondRedirect(APPNAME, URL.Howto.CREATE, error=Message.SUBMISSION_ERROR)
    except Exception as e:
        errorLog(e)
        if articleobj and not alerted:
            articleobj.delete()
        return respondRedirect(APPNAME, URL.Howto.CREATE, error=Message.SUBMISSION_ERROR)


@normal_profile_required 
def view(request: WSGIRequest, nickname: str):
    try:
        article: Article = Article.objects.get(nickname=nickname)
        if request.user.profile != article.author and article.is_draft:
            raise Exception(article)
        data = articleRenderData(request, article)
        return renderer(request, Template.Howto.ARTICLE, data)
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, error=Message.ARTICLE_NOT_FOUND)


@require_JSON
@normal_profile_required   
def draft(request: WSGIRequest, articleID:UUID):
    try:
        is_draft = request.POST.get("draft", True)
        done = Article.objects.filter(id=articleID, author=request.user.profile).update(is_draft=is_draft)
        if not done:
          return respondJson(Code.NO, error=Message.ARTICLE_NOT_FOUND)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
def topicsSearch(request: WSGIRequest, articleID: UUID) -> JsonResponse:
    """To search for topics for a article.

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

        limit = int(request.POST.get('limit', 5))
        article: Article = Article.objects.get(id=articleID, author=request.user.profile)

        cacheKey = f"article_topics_search_{query}"

        excluding = []
        if article:
            excluding = list(
                map(lambda topic: topic.id.hex, article.getTopics()))
            cacheKey = cacheKey + "".join(map(str, excluding))

        topics = cache.get(cacheKey, [])
        if not len(topics):
            topics = Topic.objects.exclude(id__in=excluding).filter(
                Q(name__istartswith=query)
                | Q(name__iendswith=query)
                | Q(name__iexact=query)
                | Q(name__icontains=query)
            )[:limit]
            cache.set(cacheKey, topics, settings.CACHE_SHORT)
        topicslist = list(map(lambda topic: dict(
            id=topic.getID(),
            name=topic.name
        ), topics[:limit]))

        return respondJson(Code.OK, dict(
            topics=topicslist
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
            if currentcount + len(addtopicIDs) > 5:
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
            if count + len(addtopics) > 5:
                if json_body:
                    return respondJson(Code.NO, error=Message.MAX_TOPICS_ACHEIVED)
                return redirect(article.getLink(error=Message.MAX_TOPICS_ACHEIVED))

            articletopics = []
            for top in addtopics:
                topic = addTopicToDatabase(
                    top, request.user.profile, article.getTags())
                articletopics.append(ArticleTopic(
                    topic=topic, article=article))
            if len(articletopics) > 0:
                ArticleTopic.objects.bulk_create(articletopics)

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

        tags = cache.get(cacheKey, [])
        if not len(tags):
            tags = Tag.objects.exclude(id__in=excludeIDs).filter(
                Q(name__istartswith=query)
                | Q(name__iendswith=query)
                | Q(name__iexact=query)
                | Q(name__icontains=query)
            )[:limit]
            cache.set(cacheKey, tags, settings.CACHE_SHORT)

        tagslist = list(map(lambda tag: dict(
            id=tag.getID(),
            name=tag.name
        ), tags[:limit]))

        return respondJson(Code.OK, dict(
            tags=tagslist
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
def tagsUpdate(request: WSGIRequest, articleID: UUID) -> HttpResponse:
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


@normal_profile_required
@require_POST
@decode_JSON
def deleteArticle(request, articleID):
    """To delete an article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the howto page if deleted successfully, else to the article page.
    """
    try:
        json_body = request.POST.get(Code.JSON_BODY, False)
        confirm = request.POST.get('confirm', False)
        if confirm:
            Article.objects.get(id=articleID, author=request.user.profile).delete()
            if json_body:
                return respondJson(Code.OK)
            return respondRedirect(APPNAME, success=Message.ARTICLE_DELETED)
        else:
                raise ValidationError(confirm)
    except (ValidationError, ObjectDoesNotExist) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        return respondRedirect(APPNAME, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def section(request: WSGIRequest, articleID: UUID, action: str):
    """To create/update/remove a section of an article

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The article's id
        action (str): The action to perform

    Raises:
        Http404: If any error occurs

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
        HttpResponseRedirect: Redirects to the articles's profile with relevant message
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    article = None
    try:
        article: Article = Article.objects.get(id=articleID, author=request.user.profile)
        if action == Action.CREATE:
            subheading = request.POST.get('subheading', "")
            paragraph = request.POST.get('paragraph', "")
            image = request.POST.get('image', None)
            video = request.POST.get('video', None)
            if not (subheading and paragraph):
                return redirect(article.getLink(error=Message.INVALID_REQUEST))

            try:
                imagefile = base64ToImageFile(image)
            except:
                imagefile = None
            try:
                videofile = base64ToFile(video)
            except:
                videofile = None

            section: Section = Section.objects.create(
                article=article,
                subheading=subheading,
                paragraph=paragraph,
                image=imagefile,
                video=videofile
            )
            return redirect(article.getLink(success=Message.SECTION_CREATED))

        id = request.POST['sectionid'][:50]
        section: Section = Section.objects.get(id=id, article=article)

        if action == Action.UPDATE:
            subheading = request.POST.get('subheading', "")
            paragraph = request.POST.get('paragraph', "")
            image = request.POST.get('image', None)
            video = request.POST.get('video', None)
            if not (subheading and paragraph):
                return redirect(article.getLink(error=Message.INVALID_REQUEST))
            changed = False
            if subheading and section.subheading != subheading:
                section.subheading = subheading
                changed = True
            if paragraph and section.paragraph != paragraph:
                section.paragraph = paragraph
                changed = True
            if image or video:
                try:
                    newimgfile = base64ToImageFile(image)
                    section.image.delete(save=False)
                    section.image = newimgfile
                    changed = True
                except:
                    newimgfile = None

                try:
                    newvidfile = base64ToFile(video)
                    section.video.delete(save=False)
                    section.video = newvidfile
                    changed = True
                except:
                    newvidfile = None
            if changed:
                section.save()
            if json_body:
                return respondJson(Code.OK, message=Message.SECTION_UPDATED)
            return redirect(article.getLink(success=Message.SECTION_UPDATED))

        if action == Action.REMOVE:
            done = section.delete()[0] >= 1
            if not done:
                raise ObjectDoesNotExist(section)
            if json_body:
                return respondJson(Code.OK, message=Message.SECTION_DELETED)
            return redirect(article.getLink(success=Message.SECTION_DELETED))

        raise KeyError(action)
    except (ObjectDoesNotExist, KeyError, ValidationError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if article:
            return redirect(article.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if article:
            return redirect(article.getLink(error=Message.INVALID_REQUEST))
        raise Http404(e)
    
    
    

