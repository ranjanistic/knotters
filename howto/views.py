from django.shortcuts import render   
from howto.models import Article 
from main.methods import renderView
from main.strings import Template

def howto(request):
    articles=Article.objects.all()
    return renderView(request, Template.HOWTO, dict(articles=articles))

def article(request, id):
    article = Article.objects.get(id = id)
    return HttpResponse(article)

