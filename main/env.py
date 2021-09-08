import environ
from pathlib import Path
import os

class Environment():
    DEVELOPMENT = 'development'
    TESTING = 'testing'
    PRODUCTION = 'production'

env = environ.Env()

environ.Env.read_env(env_file=os.path.join(Path(__file__).resolve().parent.parent, env('ENVPATH')))

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
DISCORDBOTTOKEN = env('DISCORDBOTTOKEN').strip()
SITE = env('SITE').strip()
SENDERTOKEN = env('SENDERTOKEN').strip()
STATIC_URL = env('STATIC_URL').strip()
MEDIA_URL = env('MEDIA_URL').strip()
SERVER_EMAIL = env('SERVER_EMAIL').strip()
GH_HOOK_SECRET = env('GH_HOOK_SECRET').strip()
REDIS_LOCATION = env('REDIS_LOCATION').strip()
REDIS_PASSWORD = env('REDIS_PASSWORD').strip()
RECAPTCHA_KEY=env('RECAPTCHA_KEY').strip()
RECAPTCHA_SECRET=env('RECAPTCHA_SECRET').strip()

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
SERVER_EMAIL = None if SERVER_EMAIL == 'none' else SERVER_EMAIL
GH_HOOK_SECRET = None if GH_HOOK_SECRET == 'none' else GH_HOOK_SECRET
REDIS_LOCATION = None if REDIS_LOCATION == 'none' else REDIS_LOCATION

REDIS_PORT = None if not REDIS_LOCATION else REDIS_LOCATION.split(':')[len(REDIS_LOCATION.split(':'))-1]
REDIS_HOST = None if not REDIS_LOCATION else REDIS_LOCATION.split(f":{REDIS_PORT}")[0]
REDIS_PASSWORD = None if REDIS_PASSWORD == 'none' else REDIS_PASSWORD
RECAPTCHA_KEY = None if RECAPTCHA_KEY == 'none' else RECAPTCHA_KEY
RECAPTCHA_SECRET = None if RECAPTCHA_SECRET == 'none' else RECAPTCHA_SECRET
ISPRODUCTION = ENV == Environment.PRODUCTION

ISDEVELOPMENT = ENV == Environment.DEVELOPMENT

ISTESTING = ENV == Environment.TESTING

try:
    from .__version__ import VERSION
except:
    VERSION = 'vXXX'
