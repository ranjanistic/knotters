from main.strings import Template
from .methods import renderer
from main.decorators import normal_profile_required

@normal_profile_required
def auth_index(request):
    return renderer(request, Template.Auth.INDEX)
    