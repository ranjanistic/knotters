from django.core.handlers.wsgi import WSGIRequest
from howto.models import Article, Section
from main.methods import renderView
from howto.apps import APPNAME
from django.core.exceptions import ObjectDoesNotExist


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


def articleRenderData(request:WSGIRequest, nickname: str):
    """
    Returns context data to render article page
    """
    try:
        article: Article = Article.objects.get(nickname=nickname)
        if request.user.profile != article.author and article.is_draft:
            return False
        sections = Section.objects.filter(article=article)
        self = request.user.profile==article.author and request.user.is_authenticated
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