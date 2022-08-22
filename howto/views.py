from django.shortcuts import render   
from howto.models import Article, Section
from howto.methods import renderer
from main.strings import Template, Code , Message
from main.methods import respondJson, errorLog, respondRedirect
from main.decorators import require_JSON, normal_profile_required
from .apps import APPNAME

def index(request):
    articles=Article.objects.filter(is_draft=False)
    return renderer(request, Template.Howto.INDEX, dict(articles=articles))


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
        return respondJson(Code.NO, error=Message.ERROR_OCCURRED)


def view(request, nickname:str):
    try:
        article = Article.objects.get(nickname=nickname, is_draft=False)
        sections = Section.objects.filter(article=article)
        return renderer(request, Template.Howto.ARTICLE, dict(article=article, sections=sections))
    except Exception as e:
        errorLog(e)
        return respondRedirect(APPNAME, error=Message.ERROR_OCCURRED)

    
    
    

