import environ
env = environ.Env()
environ.Env.read_env()

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


ISPRODUCTION = ENV == 'production'
