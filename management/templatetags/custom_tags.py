from random import randint
from re import sub as re_sub
from urllib.parse import unquote

from django import template
from django.utils.html import format_html
from main.methods import getNumberSuffix
from main.strings import URL, setPathParams
from people.models import Profile
from projects.models import BaseProject

register = template.Library()


@register.filter(name='params')
def replaceParams(url, params):
    return setPathParams(url, params, lookfor='\*', extendRemaining=False)


@register.filter(name='or')
def useOR(value, Or):
    return value or Or


@register.filter(name='safechars')
def safechars(value):
    return str(value).replace('\\n', '\n').replace('\"', '').replace('\\', '\"').replace('&lt;', '[').replace('&gt;', ']')


@register.filter(name='numsuffix')
def numsuffix(value):
    return f"{value}{getNumberSuffix(int(value))}"


@register.filter(name='noprotocol')
def noprotocol(link):
    if str(link).startswith(('http', 'https')):
        link = link.replace('https://', '')
        link = link.replace('http://', '')
    return link


@register.filter(name='getquery')
def getquery(url, querydata: str):
    querydata = str(querydata).replace(
        ',', '&').replace('\'', '').replace('\"', '')
    return f"{url}?{querydata}"


@register.filter(name='urldecode')
def urldecode(value):
    return unquote(value)


@register.filter(name='onezero')
def onezero(one, boolpair=None):
    if boolpair:
        yes, no = boolpair.split("|")
    else:
        yes, no = 1, 0
    return yes if one else no


@register.filter(name='publicprivateicon')
def publicprivateicon(public):
    return "lock_open" if public else "lock"


@register.simple_tag
def random_int(a=1, b=100):
    return randint(a, b)


@register.filter(name="linktags")
def linktags(text):
    """To convert hashtags, profiletags and projecttags to their respective link tags"""
    return format_html(projecttag(profiletag(amptopic(hashtag(text)))))


@register.filter(name="hashtag")
def hashtag(text):
    tags = list(filter(lambda x: x.startswith("#"), filter(lambda x: x, re_sub(
        r'[^a-zA-Z0-9\#\-\_]', " ", re_sub(r'(&#|&)+[a-z0-9A-Z]+(\;)', "", text)).split(" "))))
    tags.sort(key=lambda x: len(x), reverse=True)
    for tag in tags:
        text = text.replace(
            f"{tag}", f'<b><a href="/{URL.SEARCH}?query=tag:{tag[1:]}">{tag}</a></b>')
    return format_html(text)

@register.filter(name="amptopic")
def amptopic(text):
    topics = list(filter(lambda x: x.startswith("*"), filter(lambda x: x, re_sub(
        r'[^a-zA-Z0-9\*\-]', " ", re_sub(r'(&#|&)+[a-z0-9A-Z]+(;)', "", text)).split(" "))))
    topics.sort(key=lambda x: len(x), reverse=True)
    for topic in topics:
        text = text.replace(
            f"{topic}", f'<a href="/{URL.SEARCH}?query=topic:{topic[1:]}"><button class="small primary border-joy">{topic[1:]}</button></a>')
    return format_html(text)


@register.filter(name="profiletag")
def profiletag(text):
    tags = list(filter(lambda x: x.startswith('@'), filter(lambda x: x,
                re_sub(r'[^a-zA-Z0-9\@\-]', " ", text).split(" "))))
    tags.sort(key=lambda x: len(x), reverse=True)
    tagsdata = map(lambda tag: dict(
        profile=Profile.get_cache_one(nickname=tag[1:]), tag=tag), tags)
    tagsdata = filter(lambda tagdata: tagdata["profile"], tagsdata)
    for tagdata in tagsdata:
        text = text.replace(
            tagdata["tag"], f'<a href="{tagdata["profile"].get_link}" target="_blank"><button class="small {tagdata["profile"].theme()}" data-img="{tagdata["profile"].get_dp}">{tagdata["tag"][1:]}</button></a>')
    return format_html(text)


@register.filter(name="projecttag")
def projecttag(text):
    tags = list(filter(lambda x: x.startswith('$'), filter(
        lambda x: x, re_sub(r'[^a-zA-Z0-9\$\-]', " ", text).split(" "))))
    tags.sort(key=lambda x: len(x), reverse=True)
    tagsdata = map(lambda tag: dict(
        profile=BaseProject.get_cache_one(nickname=tag[1:]), tag=tag), tags)
    tagsdata = filter(lambda tagdata: tagdata["profile"], tagsdata)
    for tagdata in tagsdata:
        text = text.replace(
            tagdata["tag"], f'<a href="{tagdata["profile"].get_link}" target="_blank"><button class="small {tagdata["profile"].theme()}" data-img="{tagdata["profile"].get_dp}">{tagdata["tag"][1:]}</button></a>')
    return format_html(text)


@register.filter(name="urlize_blank")
def urlize_target_blank(text):
    return format_html(text.replace('<a ', '<a target="_blank" ').replace("href=\"http://", f'href="/{URL.REDIRECTOR}?n=http://').replace("href=\"https://", f'href="/{URL.REDIRECTOR}?n=https://'))


@register.filter(name='inlist')
def inlist(thelist=[], value=None):
    return value in thelist
