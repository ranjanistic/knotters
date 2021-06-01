from main.renderer import renderView
from .models import User

def index(request):
    return renderView(request,'people/index.html')

def profile(request, userID):
    user = User.objects.get(id=userID)
    return renderView(request,'people/profile.html', { "person": user })


