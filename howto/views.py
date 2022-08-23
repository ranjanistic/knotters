from django.shortcuts import redirect 
from howto.models import Article, Section
from howto.methods import renderer
from main.strings import Template, Code , Message, URL, Action
from main.methods import respondJson, errorLog, respondRedirect
from main.decorators import require_JSON, normal_profile_required
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http.response import Http404
from .apps import APPNAME

def index(request):
    articles=Article.objects.filter(is_draft=False)
    return renderer(request, Template.Howto.INDEX, dict(articles=articles))


@require_JSON
@normal_profile_required   
def draft(request, articleID:str):
    try:
        is_draft = request.POST.get("draft", True)
        done = Article.objects.filter(id=articleID).update(is_draft=is_draft)
        if not done:
          return respondJson(Code.NO, error=Message.ARTICLE_NOT_FOUND)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


def view(request, nickname:str):
    try:
        article = Article.objects.get(nickname=nickname)
        sections = Section.objects.filter(article=article)
        return renderer(request, Template.Howto.ARTICLE, dict(article=article, sections=sections))
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, error=Message.ARTICLE_NOT_FOUND)


@normal_profile_required
@require_GET
def createArticle(request):
    """To render create article page.

    METHODS: GET

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponse: The rendered text/html view.
    """
    return renderer(request, Template.Howto.CREATE)


@normal_profile_required
@require_POST
def saveArticle(request):
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
@require_POST
def deleteArticle(request, articleID):
    """To delete an article.

    METHODS: POST

    Args:
        request (WSGIRequest): The request object.

    Returns:
        HttpResponseRedirect: The redirect to the howto page if deleted successfully, else to the article page.
    """
    try:
        action = request.POST['action']
        if action == Action.REMOVE:
            Article.objects.get(id=articleID).delete()
            return respondRedirect(APPNAME, success=Message.ARTICLE_DELETED)
        else:
                raise ValidationError(action)
    except (ValidationError, ObjectDoesNotExist) as o:
        raise Http404(o)
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, error=Message.ERROR_OCCURRED)
    
    
    

