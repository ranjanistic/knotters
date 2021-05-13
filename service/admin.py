from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import Service
# Register your models here.
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ["name", "url"]
    def get_queryset(self,request):
        query_set = super(ServiceAdmin,self).get_queryset(request)
        return query_set
    class Meta:
        ordering = ("")


admin.site.register(Session)