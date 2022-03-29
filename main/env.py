from environ import Env
from pathlib import Path
from os import path as os_path

try:
    from .__version__ import VERSION
except:
    VERSION = 'vXXX'

class Environment():
    DEVELOPMENT = 'development'
    TESTING = 'testing'
    PRODUCTION = 'production'

env = Env()

Env.read_env(env_file=os_path.join(
    Path(__file__).resolve().parent.parent, env('ENVPATH')))

PROJECTKEY = env('PROJECTKEY')
PUBNAME = env('PUBNAME').strip()
ENV = env('ENV').strip()
HOSTS = env('HOSTS').split(',')
DBNAME = env('DBNAME').strip()
DBLINK = env('DBLINK').strip()
DBUSER = env('DBUSER').strip()
DBPASS = env('DBPASS').strip()
MAILUSER = env('MAILUSER').strip()
MAILPASS = env('MAILPASS').strip()
BOTMAIL = env('BOTMAIL').strip()
ADMINPATH = env('ADMINPATH').strip()
GITHUBBOTTOKEN = env('GITHUBBOTTOKEN').strip()
DISCORDSERVERID = env('DISCORDSERVER', default=None)
DISCORDBOTTOKEN = env('DISCORDBOTTOKEN').strip()
SITE = env('SITE').strip()
SENDERTOKEN = env('SENDERTOKEN').strip()
STATIC_URL = env('STATIC_URL').strip()
MEDIA_URL = env('MEDIA_URL').strip()
STATIC_ROOT = env('STATIC_ROOT').strip()
SERVER_EMAIL = env('SERVER_EMAIL').strip()
GH_HOOK_SECRET = env('GH_HOOK_SECRET').strip()
REDIS_LOCATION = env('REDIS_LOCATION').strip()
REDIS_PASSWORD = env('REDIS_PASSWORD').strip()
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
DBNAME = None if DBNAME == 'none' else DBNAME
DBLINK = None if DBLINK == 'none' else DBLINK
DBUSER = None if DBUSER == 'none' else DBUSER
DBPASS = None if DBPASS == 'none' else DBPASS
MAILUSER = None if MAILUSER == 'none' else MAILUSER
MAILPASS = None if MAILPASS == 'none' else MAILPASS
BOTMAIL = None if BOTMAIL == 'none' else BOTMAIL
ADMINPATH = None if ADMINPATH == 'none' else ADMINPATH
GITHUBBOTTOKEN = None if GITHUBBOTTOKEN == 'none' else GITHUBBOTTOKEN
DISCORDBOTTOKEN = None if DISCORDBOTTOKEN == 'none' else DISCORDBOTTOKEN
SITE = None if SITE == 'none' else SITE
SENDERTOKEN = None if SENDERTOKEN == 'none' else SENDERTOKEN
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

if ISPRODUCTION:
    STATIC_ROOT = f"{STATIC_ROOT}{VERSION}/"
    STATIC_URL = f"{STATIC_URL}{VERSION}/"
