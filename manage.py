import os
import sys

ENVPATH = 'main/.env'
ENVSAMPLEPATH = 'main/.env.example'

def main(ENVPATH):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    os.environ.setdefault('ENVPATH', ENVPATH)
    from main.env import ISPRODUCTION, ENV, DBNAME, VERSION, STATIC_ROOT, STATIC_URL
    if not ISPRODUCTION:
        print(f"Environment from: {ENVPATH}")
        print(f"Database: {DBNAME}")
        print(f"Version: {VERSION}")
        print(f"Static Root: {STATIC_ROOT}")
        print(f"Static: {STATIC_URL}")
    print(f"Environment: {ENV}")
    try:
        from django.core.management import execute_from_command_line
        
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main(ENVPATH=ENVPATH)

