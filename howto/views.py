from django.shortcuts import render   
from howto.models import Article 
from howto.methods import renderer
from main.strings import Template, Code , Message
from main.methods import respondJson, errorLog
from main.decorators import require_JSON, normal_profile_required

def index(request):
    articles=Article.objects.all()
    return renderer(request, Template.HOWTO, dict(articles=articles))

def article(request, nickname):
    article = Article.objects.get(nickname=nickname)
    return HttpResponse(article)

@require_JSON
@normal_profile_required   
def draft(request, articleID:str):
    try:
        is_draft = request.POST.get("draft", True)
        done = Article.objects.filter(id=articleID).update(is_draft=is_draft)
        if not done:
          return respondJson(Code.NO, error=Message.ARTICLE_NOT_FOUND)
        return respondJson(Code.OK)
    except Exception as e:
        errorLog(e)
        return respondJson(Code.NO, error=Message.ARTICLE_NOT_FOUND)
    
    
    

