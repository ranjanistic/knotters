from django.contrib import admin

from .forms import *
from .models import *


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "reponame", "status", 'trashed']
    list_filter = ["status", "category", 'trashed']
    search_fields = ['name']
    autocomplete_fields = ['creator','category']

    def get_queryset(self, request):
        query_set = super(ProjectAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(FreeProject)
class FProjectAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["category"]
    search_fields = ['name']
    autocomplete_fields = ['creator','category']

    def get_queryset(self, request):
        query_set = super(FProjectAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(CoreProject)
class CProjectAdmin(admin.ModelAdmin):
    list_display = ["name"]
    list_filter = ["category"]
    search_fields = ['name']
    autocomplete_fields = ['creator','category']

    def get_queryset(self, request):
        query_set = super(CProjectAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ['name']

    def get_queryset(self, request):
        query_set = super(TagAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ['name']

    def get_queryset(self, request):
        query_set = super(CategoryAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(CategoryTag)
class CategoryTagAdmin(admin.ModelAdmin):
    list_display = ["category", "tag"]
    list_filter = ["category"]
    autocomplete_fields = ['category', 'tag']

    def get_queryset(self, request):
        query_set = super(CategoryTagAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    list_display = ["project", "tag"]
    list_filter = ["project"]
    autocomplete_fields = ['project','tag']

    def get_queryset(self, request):
        query_set = super(ProjectTagAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(ProjectTopic)
class ProjectTopicAdmin(admin.ModelAdmin):
    list_display = ["project", "topic"]
    list_filter = ["project", "topic"]
    autocomplete_fields = ['project','topic']

    def get_queryset(self, request):
        query_set = super(ProjectTopicAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(LegalDoc)
class LegalDocAdmin(admin.ModelAdmin):
    list_display = ["name", "pseudonym", "icon", 'lastUpdate', 'effectiveDate']

    form = LegalDocForm

@admin.register(BaseProject)
class BaseProjectAdmin(admin.ModelAdmin):
    search_fields = ['name']
    autocomplete_fields = ['creator','category']

admin.site.register(License)
admin.site.register(ProjectSocial)
admin.site.register(BaseProjectPrimeCollaborator)
admin.site.register(BaseProjectCoCreator)
admin.site.register(FreeRepository)
admin.site.register(Snapshot)
admin.site.register(ReportedProject)
admin.site.register(ProjectAdmirer)
admin.site.register(FileExtension)
admin.site.register(ProjectTransferInvitation)
admin.site.register(CoreModerationTransferInvitation)
admin.site.register(ProjectModerationTransferInvitation)
admin.site.register(VerProjectDeletionRequest)
admin.site.register(CoreProjectDeletionRequest)
admin.site.register(AppRepository)
admin.site.register(Asset)
admin.site.register(BaseProjectCoCreatorInvitation)
admin.site.register(LeaveModerationTransferInvitation)
admin.site.register(ProjectUserRating)

@admin.register(TopicFileExtension)
class TopicFileExtensionAdmin(admin.ModelAdmin):
    list_display = ["file_extension", "topic"]
    list_filter = ["file_extension", "topic"]
