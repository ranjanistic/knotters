from django.contrib import admin
from django.contrib.sessions.models import Session
from .models import Category, Project, Relation, Tag

admin.site.register(Tag)

admin.site.register(Category)


@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_filter = ["tag", "project", "topic", "category"]
    list_display = ["tag", "project", "topic", "category"]

    def get_queryset(self, request):
        query_set = super(RelationAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "reponame", "status"]
    list_filter = ["status", "category", "creator"]

    def get_queryset(self, request):
        query_set = super(ProjectAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


admin.site.register(Session)
