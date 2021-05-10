from django.http.response import HttpResponse
from .renderer import renderView
from django.contrib.auth.decorators import login_required


def index(request):
    return renderView(request, 'index.html')

@login_required
def index2(request):
    return HttpResponse("hello")
