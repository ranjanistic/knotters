from django.contrib import admin
from .models import *
from .forms import *

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "reponame", "status", 'trashed']
    list_filter = ["status", "category", 'trashed']

    def get_queryset(self, request):
        query_set = super(ProjectAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")

@admin.register(FreeProject)
class FProjectAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["category"]

    def get_queryset(self, request):
        query_set = super(FProjectAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]

    def get_queryset(self, request):
        query_set = super(TagAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]

    def get_queryset(self, request):
        query_set = super(CategoryAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(CategoryTag)
class CategoryTagAdmin(admin.ModelAdmin):
    list_display = ["category", "tag"]
    list_filter = ["category"]

    def get_queryset(self, request):
        query_set = super(CategoryTagAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    list_display = ["project", "tag"]
    list_filter = ["project"]

    def get_queryset(self, request):
        query_set = super(ProjectTagAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(ProjectTopic)
class ProjectTopicAdmin(admin.ModelAdmin):
    list_display = ["project", "topic"]
    list_filter = ["project", "topic"]

    def get_queryset(self, request):
        query_set = super(ProjectTopicAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")

admin.site.register(License)
admin.site.register(ProjectSocial)
admin.site.register(FreeRepository)

@admin.register(LegalDoc)
class LegalDocAdmin(admin.ModelAdmin):
    list_display = ["name", "pseudonym", "icon", 'lastUpdate', 'effectiveDate']

    form = LegalDocForm
