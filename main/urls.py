from django.contrib.auth.decorators import user_passes_test
from allauth.account.decorators import login_required
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from ratelimit.decorators import ratelimit
from .strings import URL, PROJECTS, COMPETE, PEOPLE, MODERATION, MANAGEMENT
from .env import ISPRODUCTION, ADMINPATH
from .views import *
from allauth.account import views

views.signup = ratelimit(key='user_or_ip', rate='5/m',block=True, method=('POST'))(views.signup)
views.password_reset = ratelimit(key='user_or_ip', rate='5/m',block=True, method=('POST'))(views.password_reset)
views.password_reset_from_key = ratelimit(key='user_or_ip', rate='5/m',block=True, method=('POST'))(views.password_reset_from_key)
views.login = ratelimit(key='user_or_ip', rate='15/m',block=True, method=('POST'))(views.login)

admin.autodiscover()
def staff_or_404(u):
    if u.is_active and u.profile.is_active:
        if u.is_staff or u.is_admin:
            return True
    raise Http404()

admin.site.login = login_required(user_passes_test(staff_or_404)(admin.site.login))


urlpatterns = [
    path(URL.ROBOTS_TXT, Robots.as_view(), name=URL.ROBOTS_TXT),
    path(URL.MANIFEST, Manifest.as_view(), name=URL.MANIFEST),
    path(URL.SERVICE_WORKER, ServiceWorker.as_view(), name=URL.SERVICE_WORKER),
    path(URL.STRINGS, Strings.as_view(), name=URL.STRINGS),
    path(URL.SWITCH_LANG, include('django.conf.urls.i18n')),
    path(URL.VERIFY_CAPTCHA, verifyCaptcha),
    path(URL.AUTH, include('allauth_2fa.urls')),
    path(URL.AUTH, include('allauth.urls')),
    path('webpush/', include('webpush.urls')),
    path(URL.INDEX, index),
    path(URL.APPLANDING, applanding),
    path(URL.LANDING, landing),
    path(URL.OFFLINE, offline),
    path(URL.PROJECTS, include(f'{PROJECTS}.urls')),
    path(URL.COMPETE, include(f'{COMPETE}.urls')),
    path(URL.PEOPLE, include(f'{PEOPLE}.urls')),
    path(URL.MODERATION, include(f'{MODERATION}.urls')),
    path(URL.MANAGEMENT, include(f'{MANAGEMENT}.urls')),
    path(URL.REDIRECTOR, redirector),
    path(URL.DOCS, docIndex),
    path(URL.DOCTYPE, docs),
    path(URL.FAME_WALL, fameWall),
    path(URL.BROWSER, browser),
    path(URL.BASE_GITHUB_EVENTS, githubEventsListener),
    path('email/<str:template>', mailtemplate),
    path('template/<str:template>', template),
    path(ADMINPATH, admin.site.urls),
]

if not ISPRODUCTION:
    urlpatterns = urlpatterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + \
        static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
