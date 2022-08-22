from django.core.handlers.wsgi import WSGIRequest
from main.methods import renderView
from howto.apps import APPNAME
def renderer(request: WSGIRequest, file: str, data: dict = dict()):
    """Renders the given file with the given data under templates/people

    Args:
        request (WSGIRequest): The request object.
        file (str): The file to render under templates/people, without extension.
        data (dict, optional): The data to pass to the template. Defaults to dict().

    Returns:
        HttpResponse: The rendered text/html view with default and provided context.
    """
    return renderView(request, file, data, fromApp=APPNAME)