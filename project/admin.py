from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import Project, Moderator,Tag
# Register your models here.
@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "url"]
    def get_queryset(self,request):
        query_set = super(ProjectAdmin,self).get_queryset(request)
        return query_set
    class Meta:
        ordering = ("")


admin.site.register(Moderator)
admin.site.register(Tag)

admin.site.register(Session)