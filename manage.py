from os import environ
from sys import argv

ENVPATH = 'main/.env'
ENVTESTPATH = 'main/.env.testing'
ENVSAMPLEPATH = 'main/.env.example'

def main(ENVPATH):
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    try:
        from django.core.management import execute_from_command_line
        environ.setdefault('ENVPATH', ENVPATH)
        from main.env import ISPRODUCTION, ENV, DBNAME, VERSION, STATIC_ROOT, STATIC_URL, REDIS_DB
        print(f"Environment: {ENV}")
        if not ISPRODUCTION:
            print(f"Environment from: {ENVPATH}")
            print(f"Default Database: {DBNAME}")
            print(f"Redis Database: {REDIS_DB}")
            print(f"Version: {VERSION}")
            print(f"Static Root: {STATIC_ROOT}")
            print(f"Static URL: {STATIC_URL}")    
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(argv)

if __name__ == '__main__':
    if argv[1] == 'test':
        main(ENVPATH=ENVTESTPATH)
    else:
        main(ENVPATH=ENVPATH)

