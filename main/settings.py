from os import environ as os_environ
from os import path as os_path
from pathlib import Path

from . import env
from .strings import AUTH2, DB, DIVISIONS, DOCS, MANAGEMENT, PEOPLE, url

BASE_DIR = env.BASE_DIR
SECRET_KEY = env.PROJECTKEY

VERSION = env.VERSION

DEBUG = not env.ISPRODUCTION

ALLOWED_HOSTS = env.HOSTS
SERVER_EMAIL = env.SERVER_EMAIL
ADMINS = [(env.PUBNAME, env.MAIL_USERNAME)]


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
    'allauth.socialaccount.providers.linkedin_oauth2',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'allauth_2fa',
    "webpush",
    "mfa",
    "corsheaders"
] + DIVISIONS

if not env.ISTESTING:
    INSTALLED_APPS.append("django_q")

AUTH_USER_MODEL = f'{PEOPLE}.User'
SOCIALACCOUNT_ADAPTER = f'{PEOPLE}.adapter.CustomSocialAccountAdapter'

ACCOUNT_ADAPTER = 'main.adapter.CustomOTPAdapter'

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
    'csp.middleware.CSPMiddleware',
    # "main.middleware.ActivityMiddleware",
    # "main.middleware.AuthAccessMiddleware",
    "main.middleware.MinifyMiddleware",
    "main.middleware.MessageFilterMiddleware",
    "main.middleware.ProfileActivationMiddleware",
]

ROOT_URLCONF = "main.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os_path.join(BASE_DIR, "templates")],
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

if env.ISTESTING:
    PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
else:
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

DEFAULT_DB_CONFIG = {}

if env.ISTESTING:
    DEFAULT_DB_CONFIG = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",

    }
elif env.DB_AUTHMECH:
    DEFAULT_DB_CONFIG = {
        "ENGINE": "djongo",
        "CLIENT": {
            "name": env.DB_NAME,
            "host": env.DB_URL,
            "username": env.DB_USERNAME,
            "password": env.DB_PASSWORD,
            "authMechanism": env.DB_AUTHMECH,
        },
        "CONN_MAX_AGE": None
    }
else:
    DEFAULT_DB_CONFIG = {
        "ENGINE": "djongo",
        "NAME": env.DB_NAME,
        "CLIENT": {
            "host": env.DB_URL,
        },
        "CONN_MAX_AGE": None if env.ISTESTING else 0
    }


DATABASES = {
    DB.DEFAULT: DEFAULT_DB_CONFIG
}

DEFAULT_CACHE_CONFIG = {}
REDIS_CLIENT = None

if env.REDIS_LOCATION:
    DEFAULT_CACHE_CONFIG = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': env.REDIS_URL,
        'OPTIONS': {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            'PASSWORD': env.REDIS_PASSWORD,
            'db': env.REDIS_DB,
        },
        "KEY_PREFIX": env.REDIS_PREFIX,
        'TIMEOUT': None
    }
    import redis
    REDIS_CLIENT = redis.Redis(host=env.REDIS_HOST,port=env.REDIS_PORT, username=env.REDIS_USER, password=env.REDIS_PASSWORD, db=env.REDIS_DB, decode_responses=True)

if not env.ISTESTING:
    CACHES = {
        DB.DEFAULT: DEFAULT_CACHE_CONFIG
    }

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_REBOOT_THRESHOLD = 1
SESSION_EXTENSION_DAYS = 7
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CACHE_INSTANT = 15
CACHE_MICRO = CACHE_INSTANT * 4 * 2
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
    },
    'linkedin_oauth2': {
        "VERIFIED_EMAIL": True,
        'SCOPE': [
            'r_emailaddress',
            'r_liteprofile',
            # 'w_member_social',
        ],
        'PROFILE_FIELDS': [
            'id',
            'first-name',
            'last-name',
            'email-address',
            'picture-url',
            'public-profile-url',
        ]
    }
}

WSGI_APPLICATION = "main.wsgi.application"
# ASGI_APPLICATION = "main.asgi.application"

DATA_UPLOAD_MAX_MEMORY_SIZE = 10*1024*1024

STATIC_URL = env.STATIC_URL
MEDIA_ROOT = env.MEDIA_ROOT
MEDIA_URL = env.MEDIA_URL


STATICFILES_DIRS = [os_path.join(BASE_DIR, "static")]

if not env.STATIC_ROOT in STATICFILES_DIRS:
    STATIC_ROOT = env.STATIC_ROOT
elif DEBUG:
    STATIC_ROOT = env.STATIC_ROOT


CORS_ALLOWED_ORIGIN_REGEXES = [
  r"^https://\w+\.knotters\.org$"
]

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_CONFIRMATION_COOLDOWN = 60*2
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True
ACCOUNT_MAX_EMAIL_ADDRESSES = 10
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 10
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 120
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
LOGIN_URL = f'{url.getRoot(AUTH2)}{url.Auth.LOGIN}'
LOGIN_REDIRECT_URL = url.getRoot()

BYPASS_2FA_PATHS = (url.ROBOTS_TXT, url.MANIFEST, url.SCRIPTS, url.SCRIPTS_SUBAPP, url.VERSION_TXT,
                    url.SERVICE_WORKER, url.SWITCH_LANG, url.VERIFY_CAPTCHA, url.OFFLINE,
                    )

BYPASS_DEACTIVE_PATHS = BYPASS_2FA_PATHS + (
    url.REDIRECTOR,
    url.WEBPUSH_SUB,
    f"{url.getRoot(AUTH2)}{url.Auth.LOGOUT}",
    f"{url.getRoot(AUTH2)}{url.Auth.ACCOUNTACTIVATION}",
    f"{url.getRoot(DOCS)}",
    f"{url.getRoot(DOCS)}{url.Docs.TYPE}",
    f"{url.getRoot(MANAGEMENT)}{url.Management.CREATE_REPORT}",
    f"{url.getRoot(MANAGEMENT)}{url.Management.CREATE_FEED}",
)

if DEBUG:
    BYPASS_DEACTIVE_PATHS += (MEDIA_URL, STATIC_URL)

APPEND_SLASH = not False
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = f"{env.PUBNAME} Alerts <{'beta.' if env.ISBETA else ''}no-reply@knotters.org>"
EMAIL_HOST_USER = env.MAIL_USERNAME
EMAIL_HOST_PASSWORD = env.MAIL_PASSWORD
EMAIL_SUBJECT_PREFIX = env.PUBNAME
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if not DEBUG:
    os_environ["HTTPS"] = "on"
    os_environ["wsgi.url_scheme"] = "https"
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_DOMAIN = '.knotters.org'
    SESSION_COOKIE_NAME = f'{env.REDIS_PREFIX}authsessionId'
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
SITE = env.SITE

SENDER_API_HEADERS = {
    "Authorization": f"Bearer {env.SENDER_SECRET}",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

SENDER_API_URL_SUBS = "https://api.sender.net/v2/subscribers"
SENDER_API_URL_GRPS = "https://api.sender.net/v2/groups"

GITHUB_API_URL = "https://api.github.com"
GH_HOOK_SECRET = env.GH_HOOK_SECRET

GOOGLE_RECAPTCHA_KEY = env.RECAPTCHA_KEY
GOOGLE_RECAPTCHA_SECRET = env.RECAPTCHA_SECRET
GOOGLE_RECAPTCHA_API_VERIFY_SITE = "https://www.google.com/recaptcha/api/siteverify"

DISCORD_KNOTTERS_HEADERS = {
    "Authorization": env.INTERNAL_SHARED_SECRET,
    "Content-Type": "application/json",
    "Accept": "application/json",
}
DISCORD_KNOTTERS_API_URL = "https://bot.knotters.org/discord"
DISCORD_KNOTTERS_SECRET = env.DISCORDBOT_SECRET

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
        'username': env.REDIS_USER,
        'password': env.REDIS_PASSWORD,
        'db': env.REDIS_DB + 1,
    }
}


RATELIMIT_ENABLE = env.ISPRODUCTION

if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "root": {"level": "INFO", "handlers": ["file"]},
        "handlers": {
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "filename": env.env.get_value("LOGFILE", default='_logs_/server.log'),
                "formatter": "app",
                'maxBytes': 1024*1024*5,
                'backupCount': 5
            },
        },
        "loggers": {
            "django": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": True
            },
        },
        "formatters": {
            "app": {
                "format": (
                    u"%(asctime)s [%(levelname)-8s] "
                    "(%(module)s.%(funcName)s) %(message)s"
                ),
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
    }

MFA_UNALLOWED_METHODS = ()
MFA_LOGIN_CALLBACK = f"{AUTH2}.views.mfa2_login"
MFA_RECHECK = True           # Allow random rechecking of the user
MFA_RECHECK_MIN = 10         # Minimum interval in seconds
MFA_RECHECK_MAX = 30         # Maximum in seconds
MFA_QUICKLOGIN = True        # Allows quick login for returning users

# TOTP Issuer name, this should be your project's name
TOKEN_ISSUER_NAME = env.PUBNAME

if DEBUG:
    U2F_APPID = "https://localhost"
    FIDO_SERVER_ID = u"localhost"
else:
    U2F_APPID = env.SITE
    FIDO_SERVER_ID = env.HOSTS[0]

FIDO_SERVER_NAME = env.PUBNAME
MFA_REDIRECT_AFTER_REGISTRATION = url.getRoot(AUTH2)
MFA_SUCCESS_REGISTRATION_MSG = 'Your keys have successfully been created!'

INTERNAL_SHARED_SECRET = env.INTERNAL_SHARED_SECRET

CSP_STYLE_SRC = ("'self'", "'unsafe-inline'",
                 "maxcdn.bootstrapcdn.com", "*.knotters.org")

CSP_FONT_SRC = ("'self'", "data:", "maxcdn.bootstrapcdn.com", "*.knotters.org")

CSP_SCRIPT_SRC = ("'self'", "'unsafe-eval'", "*.knotters.org", "*.googletagmanager.com","*.googleoptimize.com", "*.razorpay.com")

CSP_CONNECT_SRC = ("'self'", "*.digitaloceanspaces.com", "*.google.com", "*.google.co.in",
                   "*.googletagmanager.com", "*.doubleclick.net", "*.googleoptimize.com",
                   "*.gstatic.com", "cdn.jsdelivr.net", "maxcdn.bootstrapcdn.com", "*.razorpay.com",
                   "*.gravatar.com", "*.googleusercontent.com", "*.githubusercontent.com",
                   "*.licdn.com", "*.discordapp.com", "*.knotters.org"
                   )

CSP_IMG_SRC = ("'self'", "data:", "*.digitaloceanspaces.com","*.googletagmanager.com",
               "*.gravatar.com", "*.googleusercontent.com", "*.githubusercontent.com",
               "*.licdn.com", "*.discordapp.com", "*.knotters.org"
               )

CSP_MEDIA_SRC = ("'self'","data:", "*.digitaloceanspaces.com",
               "*.gravatar.com", "*.googleusercontent.com", "*.githubusercontent.com",
               "*.licdn.com", "*.discordapp.com", "*.knotters.org")

CSP_FRAME_SRC = ("'self'", "www.google.com","*.razorpay.com", "*.knotters.org")

CSP_INCLUDE_NONCE_IN = ["script-src"]
