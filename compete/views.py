from main.renderer import renderView

def index(request):
    return renderView(request,'compete/home.html')

def competition(request, compID):
    return renderView(request,'compete/competition.html', { "compID":compID })
