import os
import sys

ENVTESTPATH = 'main/.env.testing'

def main(ENVPATH):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
    os.environ.setdefault('ENVPATH', ENVPATH)
    from main.env import ISTESTING, ENV, DBNAME, VERSION
    if not ISTESTING:
        raise Exception('Incorrectly configured environment.')
    print(f"Environment from: {ENVPATH}")
    print(f"Database: test_{DBNAME}")
    print(f"Version: {VERSION}")
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
    main(ENVPATH=ENVTESTPATH)

