from compete.models import Competition, Submission
from django.contrib import admin
from .views import *

admin.site.register(Competition)
admin.site.register(Submission)
