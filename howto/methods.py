from django.core.handlers.wsgi import WSGIRequest
from howto.models import Article, Section
from main.methods import renderView
from howto.apps import APPNAME

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


def articleRenderData(request:WSGIRequest, article: Article):
    """
    Returns context data to render article page
    """
    sections = Section.objects.filter(article=article)
    self = request.user.profile==article.author and request.user.is_authenticated
    return dict(article=article,
                sections=sections,
                self=self,
                canEdit=article.isEditable()
                )