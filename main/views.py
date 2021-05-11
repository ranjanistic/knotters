from django.http.response import HttpResponse
from .renderer import renderView
from django.contrib.auth.decorators import login_required
from service.models import Service

def index(request):
    services = Service.objects.all()
    return renderView(request, 'index.html', {"services":services})

@login_required
def index2(request):
    return HttpResponse("hello")
