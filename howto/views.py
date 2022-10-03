from django.shortcuts import redirect, render
from django.utils import timezone
from howto.models import Article, Section, ArticleTopic, ArticleTag, ArticleUserRating
from howto.methods import renderer, articleRenderData, rendererstr
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
from projects.methods import addTagToDatabase, topicSearchList, tagSearchList
from .apps import APPNAME
from django.core import serializers
from howto.mailers import articleAdmired, articleCreated , articlePublish , articleDelete
from django.db.models import Q

def index(request):
    # articles=Section.objects.filter(article__is_draft=False)

    articles=Article.objects.filter(is_draft=False)
    return renderer(request, Template.Howto.INDEX, dict(articles=articles))

    


@normal_profile_required
@require_GET
def createArticle(request: WSGIRequest):
    """To create an article.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the article page if created successfully, else 404.
    """
    try:
        if Article().canCreateArticle(request.user.profile):
            article: Article = Article.objects.create(author=request.user.profile)
            articleCreated(request, article)
            return redirect(article.getEditLink(success=Message.ARTICLE_CREATED))
        raise ValidationError(request.user.profile)
    except ValidationError as e:
        raise Http404("Unauthorised access", e)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required
@require_JSON
def saveArticle(request: WSGIRequest, nickname: str):
    """To save an article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.
        nickname (str): The nickname of the article.

    Returns:
        HttpResponseRedirect: The redirect to the article page with success message if saved successfully.
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        heading = str(request.POST["heading"]).strip()
        subheading = str(request.POST["subheading"]).strip()
        done = Article.objects.filter(nickname=nickname, author=request.user.profile).update(heading=heading, subheading=subheading)
        if not done:
            raise Exception(done)
        if json_body:
            return respondJson(Code.OK, success=Message.ARTICLE_UPDATED)
        return respondRedirect(APPNAME, path=URL.howto.view(nickname),success=Message.ARTICLE_UPDATED)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@normal_profile_required 
def view(request: WSGIRequest, nickname: str):
    """To view an article.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        nickname (str): The nickname of the article.

    Returns:
        HttpResponse: The article view
    """
    try:
        data = articleRenderData(request, nickname)
        if not data:
            raise ObjectDoesNotExist(data)
        return renderer(request, Template.Howto.ARTICLE, data)
    except ObjectDoesNotExist:
        return respondRedirect(APPNAME, error=Message.ARTICLE_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        raise Http404(e)
    
        
    
def editArticle(request: WSGIRequest, nickname: str):
    """To render edit article page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.
        nickname (str): The nickname of the article.

    Returns:
        HttpResponse: The edit article page
    """
    try:
        data = articleRenderData(request, nickname)
        if not data:
            raise ObjectDoesNotExist(data)
        return renderer(request, Template.Howto.ARTICLE_EDIT, data)
    except ObjectDoesNotExist:
        return respondRedirect(APPNAME, error=Message.ARTICLE_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_JSON
@normal_profile_required   
def publish(request: WSGIRequest, articleID:UUID):
    """To publish the article
    TODO: Add redis entry for 7 days which will be used to check editability of the article
    """
    try:
        article:Article = Article.objects.get(id=articleID, author=request.user.profile)
        articlePublish(request, article)
        if not article.heading or not article.subheading:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        articlePublish(request, article)
        article.is_draft=False
        article.modifiedOn = timezone.now()
        nickname = article.get_nickname        
        return respondJson(Code.OK, dict(nickname=nickname))
    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.ARTICLE_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


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
            # articleDelete(request, article)
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
            subheading = request.POST.get('subheading', "Untitled Section")
            paragraph = request.POST.get('paragraph', "")
            image = request.POST.get('image', None)
            video = request.POST.get('video', None)

            if not (paragraph or image or video):
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
            if json_body:
                return respondJson(Code.OK, dict(sectionID=section.id))
            return redirect(article.getLink(success=Message.SECTION_CREATED))

        id = request.POST['sectionid'][:50]
        section: Section = Section.objects.get(id=id, article=article)

        if action == Action.UPDATE:
            subheading = request.POST.get('subheading', "")
            paragraph = request.POST.get('paragraph', "")
            image = request.POST.get('image', None)
            video = request.POST.get('video', None)

            if not (subheading or paragraph or image or video):
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


@normal_profile_required
@require_JSON
def submitArticleRating(request: WSGIRequest, articleID: UUID) -> JsonResponse:
    """To submit/update/delete user rating of a article

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The article id

    Returns:
        JsonResponse: The json response with main.strings.Code.OK if task successful, or main.strings.Code.NO
    """
    try:
        action = request.POST['action']
        article: Article = Article.objects.get(id=articleID)
        profile=request.user.profile
        if action == Action.CREATE:
            score: float= float(request.POST['score'])
            if (1 <= score <= 10):
                ArticleUserRating.objects.update_or_create(profile=profile, article=article, defaults=dict(score=score))
            else:
                raise ValidationError(score)       
        elif action==Action.REMOVE:
            ArticleUserRating.objects.filter(profile=profile, article=article).delete()        
        else:
            raise ValidationError(action)
        return respondJson(Code.OK)
    except (ObjectDoesNotExist, ValidationError):
        return respondJson(Code.NO, error=Message.INVALID_REQUEST)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


@normal_profile_required
@require_POST
@decode_JSON
@ratelimit(key='user', rate='1/s', block=True, method=(Code.POST))
def toggleAdmiration(request: WSGIRequest, articleID: UUID) -> HttpResponse:
    """To toggle the admiration for a article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The id of the article

    Returns:
        JsonResponse: The response with main.strings.Code.OK if succesfull, otherwise main.strings.Code.NO
        HttpResponseRedirect: If request method was not json POST.
    """
    article = None
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        admire = request.POST['admire']
        article: Article = Article.objects.get(
            id=articleID)
        if admire in ["true", True]:
            article.admirers.add(request.user.profile)
            if(article.author.user != request.user):
                articleAdmired(request, article)
        elif admire in ["false", False]:
            article.admirers.remove(request.user.profile)
        if json_body:
            return respondJson(Code.OK)
        return redirect(article.getLink())
    except (ObjectDoesNotExist, ValidationError, KeyError) as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        if article:
            return redirect(article.getLink(error=Message.INVALID_REQUEST))
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
        if article:
            return redirect(article.getLink(error=Message.ERROR_OCCURRED))
        raise Http404(e)


@decode_JSON
def articleAdmirations(request: WSGIRequest, articleID: UUID) -> HttpResponse:
    """To get the list of admirers for a article.

    METHODS: GET, POST

    Args:
        request (WSGIRequest): The request object
        articleID (UUID): The id of the article

    Raises:
        Http404: If the article does not exist, or any other error occurs

    Returns:
        HttpResponse: The text/html reponse of admirers view with context
        JsonResponse: The response with main.strings.Code.OK and admirers list, otherwise main.strings.Code.NO
    """
    json_body = request.POST.get(Code.JSON_BODY, False)
    try:
        article: Article = Article.objects.get(
            id=articleID)
        admirers = article.admirers.filter(is_active=True, suspended=False)
        if request.user.is_authenticated:
            admirers = request.user.profile.filterBlockedProfiles(admirers)
        if json_body:
            jadmirers = list(map(lambda adm: dict(
                id=adm.get_userid,
                name=adm.get_name,
                dp=adm.get_dp,
                url=adm.get_link,
            ), admirers))
            return respondJson(Code.OK, dict(admirers=jadmirers))
        return render(request, Template().admirers, dict(admirers=admirers))
    except ObjectDoesNotExist as o:
        if json_body:
            return respondJson(Code.NO, error=Message.INVALID_REQUEST)
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        if json_body:
            return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
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
        query = request.GET.get('query', request.POST.get('query', ""))[
            :100].strip()
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
    

def renderArticle(request: WSGIRequest, nickname: str):
    """
    """
    try:
        data = articleRenderData(request, nickname)
        if not data:
            raise ObjectDoesNotExist(data)
        serialized_sections = serializers.serialize('python', data['sections'])
        return respondJson(Code.OK, dict(sections = serialized_sections))
    except ObjectDoesNotExist:
        return respondRedirect(APPNAME, error=Message.ARTICLE_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        raise Http404(e)


@require_JSON
def bulkUpdateArticle(request: WSGIRequest, articleID: str):
    """
    To bulk upadate article's sections
    """
    try:
        article:Article = Article.objects.get(id=articleID, author=request.user.profile)
        article_update = request.POST.get('article_update', None)
        section_create_paragraph = request.POST.get('section_create_paragraph', None)
        section_update = request.POST['section_update']
        
        if article_update:
            article.heading = article_update['heading']
            article.subheading = article_update['subheading']
            article.save()

        section = None
        if section_create_paragraph:
            section: Section = Section.objects.create(article=article, paragraph=section_create_paragraph, subheading="Untitled Section")

        if len(section_update)>0:
            for data in section_update:
                if data['paragraph']:
                    done = Section.objects.filter(id=data['sectionID'], article=article).update(subheading=data['subheading'], paragraph=data['paragraph'])
                else:
                    done = Section.objects.filter(id=data['sectionID'],article=article).update(subheading=section_update[0]['subheading'])
                if not done:
                    raise Exception
            
        #TODO: Try to do using bulk_update
        # if len(section_update)>0:
        #     if len(section_update)==1:
        #         if section_update[0]['paragraph']:
        #             done = Section.objects.filter(id=section_update[0]['sectionID'],article=article).update(subheading=section_update[0]['subheading'], paragraph=section_update[0]['paragraph'])
        #         else:
        #             done = Section.objects.filter(id=section_update[0]['sectionID'],article=article).update(paragraph=section_update[0]['subheading'])
        #         if not done:
        #             raise Exception
        #     else:
        #         sections_dict = {}
        #         for data in section_update:
        #             sections_dict[data['sectionID']] = [data['subheading'], data['paragraph']]
        #         update_list = Section.objects.filter(id__in=sections_dict.keys(), article=article)
        #         for obj in update_list:
        #             subheading = sections_dict[str(obj.id)][0]
        #             paragraph = sections_dict[str(obj.id)][1]
        #             obj.subheading = subheading
        #             obj.paragraph = paragraph
        #         done = Section.objects.bulk_update(update_list, ['subheading','paragraph'])
        #         if not done:
        #             raise Exception

        if section_create_paragraph:
            return respondJson(Code.OK, dict(sectionID=section.id))
        return respondJson(Code.OK)

    except ObjectDoesNotExist:
        return respondJson(Code.NO, error=Message.ARTICLE_NOT_FOUND)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)
