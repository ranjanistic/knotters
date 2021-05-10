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
CORSLIST = env('CORSLIST').split(',')
CORSTUPLE = tuple(CORSLIST)
COOKIEDOM = str(env('COOKIEDOM'))

ISPRODUCTION = ENV == 'production'
