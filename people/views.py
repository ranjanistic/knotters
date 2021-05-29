from main.renderer import renderView

def index(request):
    return renderView(request,'people/home.html')

def profile(request, userID):
    return renderView(request,'people/profile.html')


