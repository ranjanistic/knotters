from main.strings import Template
from .methods import renderer

def auth_index(request):
    return renderer(request, Template.Auth.INDEX)
    