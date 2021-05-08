from django.contrib import admin
from django.urls import path
from . import views, env

urlpatterns = [
    path(env.ADMINPATH, admin.site.urls),
    path('', views.index)
]
