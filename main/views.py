from django.views.generic import TemplateView
from django.http.response import Http404, HttpResponse, JsonResponse
from django.views.decorators.http import require_GET
from django.shortcuts import redirect
from main.settings import STATIC_URL, MEDIA_URL
from django.utils import timezone
import json
import requests
from .env import ADMINPATH, SITE
from main.strings import url
from .methods import renderData, renderView, replaceUrlParamsWithStr
from .decorators import dev_only
from projects.models import Project
from compete.models import Competition
from .methods import renderView
from .strings import code, PROJECTS, COMPETE, PEOPLE
from people.models import User
from allauth.account.models import EmailAddress

@require_GET
def offline(request):
    return renderView(request, 'offline')


@require_GET
@dev_only
def mailtemplate(request, template):
    return renderView(request, f'account/email/{template}')

@require_GET
@dev_only
def createMockUsers(request,total):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        for i in range(int(total)):
            r = requests.post(f'{SITE}/auth/signup/',headers=headers,data={'email':f"testing{i}@knotters.org","first_name":f"Testing{i}",'password1':'ABCD@12345678'})
            if r.status_code != 200:
                break
        EmailAddress.objects.filter(email__startswith=f"testing",email__endswith="@knotters.org").update(verified=True)
        return HttpResponse('ok')
    except Exception as e:
        return HttpResponse(str(e))

@require_GET
@dev_only
def clearMockUsers(request):
    User.objects.filter(email__startswith=f"testing",email__endswith="@knotters.org").delete()
    return HttpResponse('ok')

@require_GET
def index(request):
    projects = Project.objects.filter(status=code.LIVE)[0:3]
    data = {
        "projects": projects
    }
    try:
        comp = Competition.objects.get(endAt__lt=timezone.now)
        data["alert"] = {
            "message": f"The '{comp.title}' competition is on!",
            "url": f"/{COMPETE}/{comp.id}"
        }
    except:
        pass
    return renderView(request, 'index', data)


@require_GET
def redirector(request):
    next = request.GET.get('n', '/')
    next = '/' if str(next).strip() == '' or not next or next == 'None' else next
    if next.startswith("/"):
        return redirect(next)
    else: 
        return renderView(request,'forward',{'next':next})


@require_GET
def docIndex(request):
    return renderView(request, "index", fromApp='docs')


@require_GET
def docs(request, type):
    try:
        return renderView(request, type, fromApp='docs')
    except:
        raise Http404()


@require_GET
def landing(request):
    return renderView(request, "landing")

@require_GET
def applanding(request,subapp):
    return renderView(request, "landing", fromApp=subapp)


class Robots(TemplateView):
    content_type = 'text/plain'
    template_name = "robots.txt"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = {
            'admin': ADMINPATH
        }
        return context

class ServiceWorker(TemplateView):
    content_type = 'application/javascript'
    template_name = "service-worker.js"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context = renderData({
            'OFFLINE': f"/{url.OFFLINE}",
            'assets': json.dumps([
                f"/{url.OFFLINE}",
                f"{STATIC_URL}manifest.json",
                f"{STATIC_URL}html2canvas.min.js",
                f"{STATIC_URL}alertify/themes/default.min.css",
                f"{STATIC_URL}alertify/alertify.min.css",
                f"{STATIC_URL}alertify/alertify.min.js",
                f"{STATIC_URL}chartjs/chart.min.js",
                f"{STATIC_URL}cropper/cropper.min.css",
                f"{STATIC_URL}cropper/cropper.min.js",
                f"{STATIC_URL}swiper/swiper-bundle.min.css",
                f"{STATIC_URL}swiper/swiper-bundle.min.js",
                f"{STATIC_URL}fonts/Poppins/Devnagri.woff2",
                f"{STATIC_URL}fonts/Poppins/Latin.woff2",
                f"{STATIC_URL}fonts/Poppins/LatinX.woff2",
                f"{STATIC_URL}fonts/Questrial/Latin.woff2",
                f"{STATIC_URL}fonts/Questrial/LatinX.woff2",
                f"{STATIC_URL}fonts/Questrial/Vietnamese.woff2",
                f"{STATIC_URL}fonts/Poppins.css",
                f"{STATIC_URL}fonts/Questrial.css",
                f"{STATIC_URL}graphics/thirdparty/discord.png",
                f"{STATIC_URL}graphics/thirdparty/facebook.png",
                f"{STATIC_URL}graphics/thirdparty/github-dark.png",
                f"{STATIC_URL}graphics/thirdparty/github.png",
                f"{STATIC_URL}graphics/thirdparty/google.png",
                f"{STATIC_URL}graphics/thirdparty/instagram-dark.png",
                f"{STATIC_URL}graphics/thirdparty/instagram.png",
                f"{STATIC_URL}graphics/thirdparty/linkedin.png",
                f"{STATIC_URL}graphics/thirdparty/twitter.png",
                f"{STATIC_URL}icons/material.css",
                f"{STATIC_URL}icons/material.woff2",
                f"{STATIC_URL}scripts/theme.js",
                f"{STATIC_URL}scripts/index.js",
                f"{STATIC_URL}scripts/autostart.js",
                f"{STATIC_URL}styles/w3.css",
                f"{STATIC_URL}styles/theme.css",
                f"{STATIC_URL}styles/overrides.css",
                f"{STATIC_URL}styles/scrollbar.css",
                f"{STATIC_URL}styles/loader.css",
                f"{STATIC_URL}styles/index.css",
            ]),
            'noOfflineList': json.dumps([
                replaceUrlParamsWithStr(
                    f"/{url.COMPETE}{url.Compete.COMPETETABSECTION}"),
                replaceUrlParamsWithStr(
                    f"/{url.COMPETE}{url.Compete.INDEXTAB}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.SETTINGTAB}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.PROFILETAB}"),
            ]),
            'ignorelist': json.dumps([
                f"/{ADMINPATH}*",
                f"/{ADMINPATH}",
                f"/{url.ROBOTS_TXT}",
                f"{MEDIA_URL}*",
                f"/{url.REDIRECTOR}*",
                f"/{url.ACCOUNTS}*",
                f"/{url.MODERATION}*",
                f"/{url.COMPETE}*",
                f"/{url.LANDING}",
                replaceUrlParamsWithStr(f"/{url.APPLANDING}"),
                replaceUrlParamsWithStr(f"/{url.DOCTYPE}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.CREATE}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.PROJECTINFO}"),
            ]),
            'recacheList': json.dumps([
                f"/{url.REDIRECTOR}*",
                f"/{url.ACCOUNTS}*",
                replaceUrlParamsWithStr(
                    f"/{url.COMPETE}{url.Compete.INVITEACTION}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.PROFILEEDIT}"),
                replaceUrlParamsWithStr(
                    f"/{url.PEOPLE}{url.People.ACCOUNTPREFERENCES}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.PROFILEEDIT}"),
            ]),
        })
        return context
