from django import template
from main.strings import setPathParams

register = template.Library()


@register.filter
def addstr(arg1, arg2):
    """concatenate arg1 & arg2"""
    return str(arg1) + str(arg2)


@register.filter(name='params')
def replaceParams(url, params):
    return setPathParams(url, params, lookfor='\*', extendRemaining=False)
