from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import Service
# Register your models here.
admin.site.register(Service)
admin.site.register(Session)