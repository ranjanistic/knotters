from django import template
from urllib.parse import unquote
from main.methods import getNumberSuffix
from main.strings import setPathParams

register = template.Library()


@register.filter(name='params')
def replaceParams(url,params):
    return setPathParams(url,params,lookfor='\*',extendRemaining=False)

@register.filter(name='or')
def useOR(value,Or):
    return value or Or


@register.filter(name='safechars')
def safechars(value):
    return str(value).replace('\\n','\n').replace('\"','').replace('\\','\"').replace('&lt;','[').replace('&gt;',']')

@register.filter(name='numsuffix')
def numsuffix(value):
    return f"{value}{getNumberSuffix(int(value))}"

@register.filter(name='noprotocol')
def noprotocol(link):
    if str(link).startswith(('http','https')):
        link = link.replace('https://','')
        link = link.replace('http://','')
    return link

@register.filter(name='getquery')
def getquery(url,querydata:str):
    querydata = str(querydata).replace(',','&').replace('\'','').replace('\"','')
    return f"{url}?{querydata}"

@register.filter(name='urldecode')
def urldecode(value):
    return unquote(value)
