from main.renderer import renderView
from django.views.decorators.http import require_GET, require_POST

@require_GET
def index(request):
    return renderView(request,'compete/home.html')

@require_GET
def competition(request, compID):
    return renderView(request,'compete/competition.html', { "compID":compID })
