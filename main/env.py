import environ
from .strings import environment
from pathlib import Path
import os

env = environ.Env()

environ.Env.read_env(env_file=os.path.join(Path(__file__).resolve().parent.parent, env('ENVPATH')))

PUBNAME = env('PUBNAME')
PROJECTKEY = env('PROJECTKEY')
PUBNAME = env('PUBNAME')
ENV = env('ENV')
HOSTS = env('HOSTS').split(',')
DBNAME = env('DBNAME')
DBLINK = env('DBLINK')
DBUSER = env('DBUSER')
DBPASS = env('DBPASS')
MAILUSER = env('MAILUSER')
MAILPASS = env('MAILPASS')
ADMINPATH = env('ADMINPATH')
GITHUBBOTTOKEN = env('GITHUBBOTTOKEN')
SITE = env('SITE')
SENDERTOKEN = env('SENDERTOKEN')
STATIC_URL = env('STATIC_URL')
MEDIA_URL = env('MEDIA_URL')

ISPRODUCTION = ENV == environment.PRODUCTION

VERSION = 'v-10'
    
if ISPRODUCTION:
    from main.__version__ import VERSION as V
    VERSION = V