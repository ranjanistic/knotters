"""
Loads environment variables from file path specified in ENVPATH environment variable beforehand (generally main/.env).
"""
from os import path as os_path
from pathlib import Path

from environ import Env

try:
    from .__version__ import VERSION
except:
    VERSION = 'vXXX'


class Environment():
    DEVELOPMENT = 'development'
    TESTING = 'testing'
    PRODUCTION = 'production'


env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent

Env.read_env(env_file=os_path.join(BASE_DIR, env('ENVPATH')))

PROJECTKEY = env('PROJECTKEY')
PUBNAME = env('PUBNAME').strip()
ENV = env('ENV').strip()
HOSTS = env('HOSTS').split(',')
DB_NAME = env('DB_NAME').strip()
DB_URL = env('DB_URL').strip()
DB_USERNAME = env('DB_USERNAME').strip()
DB_PASSWORD = env('DB_PASSWORD').strip()
DB_AUTHMECH = env('DB_AUTHMECH').strip()
MAIL_USERNAME = env('MAIL_USERNAME').strip()
MAIL_PASSWORD = env('MAIL_PASSWORD').strip()
BOTMAIL = env('BOTMAIL').strip()
ADMINPATH = env('ADMINPATH').strip()
GITHUBBOT_SECRET = env('GITHUBBOT_SECRET', default=None)
DISCORDSERVERID = env('DISCORDSERVER', default=None)
DISCORDBOT_SECRET = env('DISCORDBOT_SECRET', default=None)
SITE = env('SITE').strip()
SENDER_SECRET = env('SENDER_SECRET').strip()
STATIC_URL = env('STATIC_URL').strip()
MEDIA_URL = env('MEDIA_URL').strip()
STATIC_ROOT = env('STATIC_ROOT').strip()
MEDIA_ROOT = env('MEDIA_ROOT', default=os_path.join(BASE_DIR, 'media')).strip()
SERVER_EMAIL = env('SERVER_EMAIL').strip()
GH_HOOK_SECRET = env('GH_HOOK_SECRET').strip()
REDIS_LOCATION = env('REDIS_LOCATION').strip()
REDIS_PASSWORD = env('REDIS_PASSWORD').strip()
REDIS_USER = env('REDIS_USER', default='default').strip()
REDIS_DB = env('REDIS_DB', default='1').strip()
RECAPTCHA_KEY = env('RECAPTCHA_KEY').strip()
RECAPTCHA_SECRET = env('RECAPTCHA_SECRET').strip()
VAPID_PUBLIC_KEY = env('VAPID_PUBLIC_KEY').strip()
VAPID_PRIVATE_KEY = env('VAPID_PRIVATE_KEY').strip()
VAPID_ADMIN_MAIL = env('VAPID_ADMIN_MAIL').strip()
LOCALE_ABS_PATH = env('LOCALE_ABS_PATH').strip()
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS').split(',')
GSUITE_CREDENTIALS_PATH = env('GSUITE_CREDENTIALS_PATH', default=None)

CDN_URL = env('CDN_URL', default='https://cdn.knotters.org').strip()
INTERNAL_SHARED_SECRET = env(
    'INTERNAL_SHARED_SECRET', default='secret').strip()

PROJECTKEY = None if PROJECTKEY == 'none' else PROJECTKEY
PUBNAME = None if PUBNAME == 'none' else PUBNAME
ENV = None if ENV == 'none' else ENV
HOSTS = None if HOSTS == 'none' else HOSTS
DB_NAME = None if DB_NAME == 'none' else DB_NAME
DB_URL = None if DB_URL == 'none' else DB_URL
DB_USERNAME = None if DB_USERNAME == 'none' else DB_USERNAME
DB_PASSWORD = None if DB_PASSWORD == 'none' else DB_PASSWORD
MAIL_USERNAME = None if MAIL_USERNAME == 'none' else MAIL_USERNAME
MAIL_PASSWORD = None if MAIL_PASSWORD == 'none' else MAIL_PASSWORD
BOTMAIL = None if BOTMAIL == 'none' else BOTMAIL
ADMINPATH = None if ADMINPATH == 'none' else ADMINPATH
GITHUBBOT_SECRET = None if GITHUBBOT_SECRET == 'none' else GITHUBBOT_SECRET
DISCORDBOT_SECRET = None if DISCORDBOT_SECRET == 'none' else DISCORDBOT_SECRET
SITE = None if SITE == 'none' else SITE
SENDER_SECRET = None if SENDER_SECRET == 'none' else SENDER_SECRET
MEDIA_URL = None if MEDIA_URL == 'none' else MEDIA_URL
STATIC_URL = None if STATIC_URL == 'none' else STATIC_URL
STATIC_ROOT = None if STATIC_ROOT == 'none' else STATIC_ROOT
SERVER_EMAIL = None if SERVER_EMAIL == 'none' else SERVER_EMAIL
GH_HOOK_SECRET = None if GH_HOOK_SECRET == 'none' else GH_HOOK_SECRET
REDIS_LOCATION = None if REDIS_LOCATION == 'none' else REDIS_LOCATION

REDIS_PORT = None if not REDIS_LOCATION else REDIS_LOCATION.split(
    ':')[len(REDIS_LOCATION.split(':'))-1]
REDIS_HOST = None if not REDIS_LOCATION else REDIS_LOCATION.split(f":{REDIS_PORT}")[
    0]
REDIS_PASSWORD = None if REDIS_PASSWORD == 'none' else REDIS_PASSWORD
REDIS_DB = 1 if REDIS_DB == 'none' else int(REDIS_DB)
RECAPTCHA_KEY = None if RECAPTCHA_KEY == 'none' else RECAPTCHA_KEY
RECAPTCHA_SECRET = None if RECAPTCHA_SECRET == 'none' else RECAPTCHA_SECRET

VAPID_PUBLIC_KEY = None if VAPID_PUBLIC_KEY == 'none' else VAPID_PUBLIC_KEY
VAPID_PRIVATE_KEY = None if VAPID_PRIVATE_KEY == 'none' else VAPID_PRIVATE_KEY
VAPID_ADMIN_MAIL = None if VAPID_ADMIN_MAIL == 'none' else VAPID_ADMIN_MAIL
LOCALE_ABS_PATH = None if LOCALE_ABS_PATH == 'none' else LOCALE_ABS_PATH
GSUITE_CREDENTIALS_PATH = None if GSUITE_CREDENTIALS_PATH == 'none' else GSUITE_CREDENTIALS_PATH

ASYNC_CLUSTER = REDIS_PORT and REDIS_HOST

ISPRODUCTION = ENV == Environment.PRODUCTION

ISDEVELOPMENT = ENV == Environment.DEVELOPMENT

ISTESTING = ENV == Environment.TESTING

ISBETA = HOSTS and HOSTS[0].startswith('beta.')

STATIC_URL = f"{STATIC_URL}{VERSION}/"

if ISPRODUCTION:
    STATIC_ROOT = f"{STATIC_ROOT}{VERSION}/"
