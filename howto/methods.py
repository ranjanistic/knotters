from django.core.handlers.wsgi import WSGIRequest
from howto.models import Article, Section
from main.methods import errorLog, renderView, renderString
from howto.apps import APPNAME
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse


def renderer(request: WSGIRequest, file: str, data: dict = dict()):
    """Renders the given file with the given data under templates/howto

    Args:
        request (WSGIRequest): The request object.
        file (str): The file to render under templates/howto, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        HttpResponse: The rendered text/html view with default and provided context.
    """
    return renderView(request, file, data, fromApp=APPNAME)


def rendererstr(request: WSGIRequest, file: str, data: dict = dict()) -> HttpResponse:
    """Returns text/html content as http response with the given data.

    Args:
        request (WSGIRequest): The request object.
        file (str): The file for html content under templates/projects, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        HttpResponse: The text based html string content http response with default and provided context.
    """
    return HttpResponse(renderString(request, file, data, fromApp=APPNAME))


def articleRenderData(request:WSGIRequest, nickname: str):
    """
    Returns context data to render article page
    """
    try:

        article: Article = Article.get_cache_one(nickname)
        if not article:
            raise ObjectDoesNotExist(article)
        authenticated = request.user.is_authenticated
        self: bool = authenticated and request.user.profile == article.author
        if not self and article.is_draft:
            return False
        sections = article.getSections()
        isAdmirer = request.user.is_authenticated and article.isAdmirer(
            request.user.profile)
        isRater = False if not request.user.is_authenticated else article.is_rated_by(
            profile=request.user.profile)
        userRatingScore = 0 if not request.user.is_authenticated else article.rating_by_user(profile=request.user.profile)
        return dict(article=article,
                    sections=sections,
                    self=self,
                    userRatingScore=userRatingScore,
                    isRater=isRater,
                    isAdmirer=isAdmirer
                    )
    except ObjectDoesNotExist:
        return False