from django import template
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

