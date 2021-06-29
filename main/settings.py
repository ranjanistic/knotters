import os
from pathlib import Path
from . import env
from .strings import DIVISIONS, PEOPLE

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env.PROJECTKEY

VERSION = env.VERSION

DEBUG = not env.ISPRODUCTION

ALLOWED_HOSTS = env.HOSTS

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    'allauth.socialaccount.providers.github',
    'allauth.socialaccount.providers.discord',
] + DIVISIONS

AUTH_USER_MODEL = f'{PEOPLE}.User'
SOCIALACCOUNT_ADAPTER = f'{PEOPLE}.adapter.CustomSocialAccountAdapter'

ACCOUNT_FORMS = {
    'signup': f'{PEOPLE}.forms.CustomSignupForm',
}

SOCIALACCOUNT_QUERY_EMAIL = True

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
DBBACKUP_STORAGE = "django.core.files.storage.FileSystemStorage"
DBBACKUP_STORAGE_OPTIONS = {"location": os.path.join(BASE_DIR, "backup")}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "main.urls"


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "main.context_processors.Global",
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

if not DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "djongo",
            "CLIENT": {
                "name": env.DBNAME,
                "host": env.DBLINK,
                "username": env.DBUSER,
                "password": env.DBPASS,
                "authMechanism": "SCRAM-SHA-1",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "djongo",
            "NAME": env.DBNAME,
            "CLIENT": {
                "host": env.DBLINK,
            },
        }
    }

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'github': {
        "VERIFIED_EMAIL": True,
        'SCOPE': [
            'email',
            'user',
            'repo',
        ],
    }
}

WSGI_APPLICATION = "main.wsgi.application"

DATA_UPLOAD_MAX_MEMORY_SIZE=10*1024*1024

STATIC_URL = env.STATIC_URL
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = env.MEDIA_URL

if DEBUG:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")

CORS_ORIGIN_ALLOW_ALL = False

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 50
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
LOGIN_REDIRECT_URL = '/'

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = env.MAILUSER
EMAIL_HOST_USER = env.MAILUSER
EMAIL_HOST_PASSWORD = env.MAILPASS
EMAIL_SUBJECT_PREFIX = env.PUBNAME
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SENDER_API_HEADERS = {
    "Authorization": f"Bearer {env.SENDERTOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}
SENDER_API_URL_SUBS = "https://api.sender.net/v2/subscribers"
SENDER_API_URL_GRPS = "https://api.sender.net/v2/groups"

if not DEBUG:
    os.environ["HTTPS"] = "on"
    os.environ["wsgi.url_scheme"] = "https"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = env.HOSTS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_REFERRER_POLICY = "same-origin"
    SECURE_HSTS_PRELOAD = True

FIRST_DAY_OF_WEEK = 1
DEFAULT_CHARSET = 'utf-8'
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_L10N = True
USE_TZ = True

SITE_ID = 2
