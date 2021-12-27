import os
from pathlib import Path
from .strings import url, DIVISIONS, PEOPLE, AUTH
from . import env

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = env.PROJECTKEY

VERSION = env.VERSION

DEBUG = not env.ISPRODUCTION

ALLOWED_HOSTS = env.HOSTS
SERVER_EMAIL = env.SERVER_EMAIL
ADMINS = [(env.PUBNAME, env.MAILUSER)]

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
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'allauth_2fa',
    "webpush",
    "django_q"
] + DIVISIONS

AUTH_USER_MODEL = f'{PEOPLE}.User'
SOCIALACCOUNT_ADAPTER = f'{PEOPLE}.adapter.CustomSocialAccountAdapter'

ACCOUNT_ADAPTER = 'allauth_2fa.adapter.OTPAdapter'

ACCOUNT_FORMS = {
    'signup': f'{PEOPLE}.forms.CustomSignupForm',
}

SOCIALACCOUNT_QUERY_EMAIL = True

STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "main.middleware.ExtendedSessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "main.middleware.XForwardedForMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'django_otp.middleware.OTPMiddleware',
    'main.middleware.TwoFactorMiddleware',
    "django.contrib.messages.middleware.MessageMiddleware",
    "main.middleware.ProfileActivationMiddleware",
    # "main.middleware.ActivityMiddleware",
    # "main.middleware.AuthAccessMiddleware",
    "main.middleware.MessageFilterMiddleware",
]

ROOT_URLCONF = "main.urls"

BYPASS_2FA_PATHS = (url.ROBOTS_TXT, url.MANIFEST, url.STRINGS,
                    url.SERVICE_WORKER, url.SWITCH_LANG, url.VERIFY_CAPTCHA)

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
                "django.template.context_processors.i18n",
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

VAPID_PUBLIC_KEY = env.VAPID_PUBLIC_KEY

WEBPUSH_SETTINGS = {
   "VAPID_PUBLIC_KEY": VAPID_PUBLIC_KEY,
   "VAPID_PRIVATE_KEY": env.VAPID_PRIVATE_KEY,
   "VAPID_ADMIN_EMAIL": env.VAPID_ADMIN_MAIL,
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.MD5PasswordHasher',
    'django.contrib.auth.hashers.CryptPasswordHasher'
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

DB_HOST_API = env.DBLINK

if not DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "djongo",
            "CLIENT": {
                "name": env.DBNAME,
                "host": DB_HOST_API,
                "username": env.DBUSER,
                "password": env.DBPASS,
                "authMechanism": "SCRAM-SHA-1",
            },
            "CONN_MAX_AGE": None
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "djongo",
            "NAME": env.DBNAME,
            "CLIENT": {
                "host": DB_HOST_API,
            },
            "CONN_MAX_AGE": None if env.ISTESTING else 0
        }
    }

if not env.ISTESTING and env.ASYNC_CLUSTER:
    CACHES = {
        'default': {} if not env.REDIS_LOCATION else {
            'BACKEND': 'redis_cache.RedisCache',
            'LOCATION': env.REDIS_LOCATION,
            'OPTIONS': {} if not env.REDIS_PASSWORD else {
                'PASSWORD': env.REDIS_PASSWORD,
            }
        },
    }

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_REBOOT_THRESHOLD = 1
SESSION_EXTENSION_DAYS = 7
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CACHE_MICRO = 60 * 2
CACHE_MIN = CACHE_MICRO * 3
CACHE_SHORT = CACHE_MIN * 3
CACHE_LONG = CACHE_SHORT * 2
CACHE_LONGER = CACHE_LONG * 2
CACHE_MAX = CACHE_LONGER * 2
CACHE_ETERNAL = CACHE_MAX * 12 * 6

CACHE_MINI = CACHE_MIN

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        "VERIFIED_EMAIL": True,
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
# ASGI_APPLICATION = "main.asgi.application"

DATA_UPLOAD_MAX_MEMORY_SIZE = 10*1024*1024

STATIC_URL = env.STATIC_URL
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = env.MEDIA_URL


STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

if not env.STATIC_ROOT in STATICFILES_DIRS:
    STATIC_ROOT = env.STATIC_ROOT
elif DEBUG:
    STATIC_ROOT = env.STATIC_ROOT


CORS_ORIGIN_ALLOW_ALL = False

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory" if env.ISPRODUCTION else "none"
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 50
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 300
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
# LOGIN_URL = 'two_factor:login'
# LOGIN_REDIRECT_URL = 'two_factor:profile'
LOGIN_URL = f'{url.getRoot(AUTH)}{url.Auth.LOGIN}'
LOGIN_REDIRECT_URL = url.getRoot()

APPEND_SLASH = not False
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = f"{env.PUBNAME} <{env.MAILUSER}>"
EMAIL_HOST_USER = env.MAILUSER
EMAIL_HOST_PASSWORD = env.MAILPASS
EMAIL_SUBJECT_PREFIX = env.PUBNAME
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

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
    DEFAULT_HTTP_PROTOCOL = "https"
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"

FIRST_DAY_OF_WEEK = 1
DEFAULT_CHARSET = 'utf-8'
LANGUAGE_CODE = "en"
LANGUAGE_COOKIE_NAME = "client_language"
LANGUAGE_COOKIE_SECURE = True
LANGUAGES = (
    ('af', 'Afrikaans'),
    ('ar', 'عربي'),
    ('ast', 'Asturian'),
    ('az', 'Azərbaycanca'),
    ('bg', 'български'),
    ('be', 'Беларуская'),
    ('bn', 'বাংলা'),
    ('br', 'Breton'),
    ('bs', 'Bosanski'),
    ('ca', 'Català'),
    ('cs', 'čeština'),
    ('cy', 'Cymraeg'),
    ('da', 'dansk'),
    ('de', 'Deutsch'),
    ('dsb', 'Lower Sorbian'),
    ('el', 'Ελληνικά'),
    ('en', 'English'),
    ('en-au', 'Australian English'),
    ('en-gb', 'British English'),
    ('eo', 'Esperanto'),
    ('es', 'Español'),
    ('es-ar', 'Argentinian Spanish'),
    ('es-co', 'Colombian Spanish'),
    ('es-mx', 'Mexican Spanish'),
    ('es-ni', 'Nicaraguan Spanish'),
    ('es-ve', 'Venezuelan Spanish'),
    ('et', 'Eestlane'),
    ('eu', 'Euskara'),
    ('fa', 'فارسی'),
    ('fi', 'Suomalainen'),
    ('fr', 'français'),
    ('fy', 'Frysk'),
    ('ga', 'Gaeilge'),
    ('gd', 'Gàidhlig na h-Alba'),
    ('gl', 'Galego'),
    ('he', 'Hebrew'),
    ('hi', 'हिंदी'),
    ('hr', 'Hrvatski'),
    ('hsb', 'Upper Sorbian'),
    ('hu', 'Magyar'),
    ('hy', 'հայերեն'),
    ('ia', 'Interlingua'),
    ('id', 'bahasa Indonesia'),
    ('io', 'Ido'),
    ('is', 'Íslensku'),
    ('it', 'italiano'),
    ('ja', '日本'),
    ('ka', 'ქართული'),
    ('kab', 'Kabyle'),
    ('kk', 'Қазақша'),
    ('km', 'ខ្មែរ'),
    ('kn', 'ಕನ್ನಡ'),
    ('ko', '한국인'),
    ('lb', 'Lëtzebuergesch'),
    ('lt', 'Lietuvių'),
    ('lv', 'Latvietis'),
    ('mk', 'Македонски'),
    ('ml', 'മലയാളം'),
    ('mn', 'Монгол'),
    ('mr', 'मराठी'),
    ('my', 'ဗမာ'),
    ('nb', 'Norwegian Bokmål'),
    ('ne', 'नेपाली'),
    ('nl', 'Nederlands'),
    ('nn', 'Norwegian Nynorsk'),
    ('os', 'Ossetic'),
    ('pa', 'ਪੰਜਾਬੀ'),
    ('pl', 'Polskie'),
    ('pt', 'português'),
    ('pt-br', 'Brazilian Portuguese'),
    ('ro', 'Română'),
    ('ru', 'русский'),
    ('sk', 'Slovenský'),
    ('sl', 'Slovenščina'),
    ('sq', 'Shqiptare'),
    ('sr', 'Српски'),
    ('sr-latn', 'Serbian Latin'),
    ('sv', 'svenska'),
    ('sw', 'Kiswahili'),
    ('ta', 'தமிழ்'),
    ('te', 'తెలుగు'),
    ('th', 'ไทย'),
    ('tr', 'Türk'),
    ('tt', 'Tatar'),
    ('udm', 'Udmurt'),
    ('uk', 'Українська'),
    ('ur', 'اردو'),
    ('uz', "O'zbek"),
    ('vi', 'Tiếng Việt'),
    ('zh-hans', 'Simplified Chinese'),
    ('zh-hant', 'Traditional Chinese'),

)

TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_L10N = True
USE_TZ = True

TRANSLATIONS_PROJECT_BASE_DIR = Path(env.LOCALE_ABS_PATH).resolve()

LOCALE_PATHS = (TRANSLATIONS_PROJECT_BASE_DIR,)

TRANSLATIONS_ADMIN_EXCLUDE_FIELDS = ['get_hint', 'locale_parent_dir', 'domain']

SITE_ID = 1

SENDER_API_HEADERS = {
    "Authorization": f"Bearer {env.SENDERTOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

SENDER_API_URL_SUBS = "https://api.sender.net/v2/subscribers"
SENDER_API_URL_GRPS = "https://api.sender.net/v2/groups"

GITHUB_API_URL = "https://api.github.com"
GH_HOOK_SECRET = env.GH_HOOK_SECRET


GOOGLE_RECAPTCHA_SECRET_KEY = env.RECAPTCHA_SECRET
GOOGLE_RECAPTCHA_VERIFY_SITE = "https://www.google.com/recaptcha/api/siteverify"

if env.ASYNC_CLUSTER:
    Q_CLUSTER = {
        'name': env.PUBNAME,
        'workers': 8,
        'recycle': 500,
        'timeout': 60,
        'retry': 70,
        'sync': env.ISTESTING,
        'compress': True,
        'save_limit': 250,
        'queue_limit': 500,
        'cpu_affinity': 1,
        'max_attempts': 10,
        'label': f"{env.PUBNAME} Django Q",
        'redis':  {
            'host': env.REDIS_HOST,
            'port': env.REDIS_PORT,
            'password': env.REDIS_PASSWORD,
            'db': 2,
        }
    }


RATELIMIT_ENABLE = env.ISPRODUCTION
