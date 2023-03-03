#!~/Env/knotters/bin python3
# -*- coding: utf-8 -*-

from multiprocessing import cpu_count
import sys
import os
from main.__version__ import VERSION
from os import environ

print(VERSION)
print(sys.prefix)
environ.setdefault('ENVPATH', 'main/.env')

wsgi_app = "main.wsgi:application"
capture_output = True
pidfile = "/var/www/gunicorn/knotters.pid"
bind = "unix:/var/www/sockets/knotters.gunicorn.sock"
max_requests = 1000
accesslog = "/var/log/gunicorn/knotters.access.log"
errorlog = "/var/log/gunicorn/knotters.error.log"
worker_class = 'gevent'
workers = cpu_count()
