from django.views.generic import TemplateView
from django.http.response import Http404, HttpResponse
from django.views.decorators.http import require_GET
from django.shortcuts import redirect
from main.settings import STATIC_URL, MEDIA_URL
import json
from main.strings import url
from .methods import renderData, renderView, replaceUrlParamsWithStr
from .decorators import dev_only
from projects.models import Project
from compete.models import Competition
from .methods import renderView
from .strings import code, PROJECTS, COMPETE, PEOPLE


@require_GET
def offline(request):
    return renderView(request, 'offline')


@require_GET
@dev_only
def mailtemplate(request, template):
    return renderView(request, f'account/email/{template}')


@require_GET
def index(request):
    projects = Project.objects.filter(status=code.LIVE)[0:3]
    data = {
        "projects": projects
    }
    try:
        comp = Competition.objects.get(active=True)
        data["alert"] = {
            "message": f"The '{comp.title}' competition is on!",
            "url": f"/competitions/{comp.id}"
        }
    except:
        pass
    return renderView(request, 'index', data)


@require_GET
def redirector(request):
    next = request.GET.get('n', '/')
    next = '/' if str(next).strip() == '' or not next else next
    return redirect(next) if next.startswith("/") else HttpResponse(f"<h1>Redirecting to {next}</h1><script>window.location.replace('{next}')</script>")


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
    parts = request.build_absolute_uri().split('/')
    try:
        subapp = parts[len(parts)-2]
        if not [PEOPLE, PROJECTS, COMPETE].__contains__(subapp):
            subapp = ''
        return renderView(request, "landing", fromApp=subapp)
    except:
        raise Http404()


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
                f"{STATIC_URL}alertify/themes/default.min.css",
                f"{STATIC_URL}alertify/alertify.min.css",
                f"{STATIC_URL}alertify/alertify.min.js",
                f"{STATIC_URL}chartjs/chart.min.js",
                f"{STATIC_URL}cropper/cropper.min.css",
                f"{STATIC_URL}cropper/cropper.min.js",
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
                f"{MEDIA_URL}*",
                f"/{url.REDIRECTOR}*",
                f"/{url.ACCOUNTS}*",
                f"/{url.LANDING}",
                f"/*/{url.LANDING}",
                replaceUrlParamsWithStr(f"/{url.DOCTYPE}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.CREATE}"),
                replaceUrlParamsWithStr(
                    f"/{url.PROJECTS}{url.Projects.PROJECTINFO}"),
            ]),
            'recacheList': json.dumps([
                f"/{url.REDIRECTOR}*",
            ]),
        })
        return context
