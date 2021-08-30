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

REDIS_LOCATION = None if REDIS_LOCATION == 'none' else REDIS_LOCATION
REDIS_PASSWORD = None if REDIS_PASSWORD == 'none' else REDIS_PASSWORD

ISPRODUCTION = ENV == Environment.PRODUCTION

ISDEVELOPMENT = ENV == Environment.DEVELOPMENT

ISTESTING = ENV == Environment.TESTING

VERSION = 'v--16'

if ISPRODUCTION:
    from .__version__ import VERSION as V
    VERSION = V