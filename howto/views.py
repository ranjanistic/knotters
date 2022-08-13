from django.shortcuts import render   
from howto.models import Article 
from main.methods import renderView
from main.strings import Template

def index(request):
    articles=Article.objects.all()
    return renderView(request, Template.HOWTO, dict(articles=articles))

def article(request, nickname):
    article = Article.objects.get(nickname=nickname)
    return HttpResponse(article)

def draft(request, articleID):
    
    

