from pathlib import Path
import os
from . import env

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = env.PROJECTKEY

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
    "project",
    "compete",
    "people",
    "moderation",
]

AUTH_USER_MODEL = 'people.User'
SOCIALACCOUNT_ADAPTER = 'people.adapter.CustomSocialAccountAdapter'

ACCOUNT_FORMS = {
    'signup': 'people.forms.CustomSignupForm',
}

SOCIALACCOUNT_QUERY_EMAIL=True

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
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "main.wsgi.application"


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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = "/static/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

CORS_ORIGIN_ALLOW_ALL = False

if not env.ISPRODUCTION:
  STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]
else:
  STATIC_ROOT = os.path.join(BASE_DIR, "static")

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 50
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env.MAILUSER
EMAIL_HOST_PASSWORD = env.MAILPASS
EMAIL_SUBJECT_PREFIX = 'Knotters Community'
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_REDIRECT_URL = '/'

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



SITE_ID = 2


AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

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
        'SCOPE': [
            'email',
            'user',
            'repo',
            'read:org',
        ],
    }

}
