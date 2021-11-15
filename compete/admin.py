from django.contrib import admin
from .forms import CompetitionAdminForm, ResultAdminForm, JudgePanelForm
from compete.models import *


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["title", "tagline", "isHistory",
                    "startAt", "endAt", "banner", "resultDeclared"]
    list_filter = ["resultDeclared", "eachTopicMaxPoint"]
    ordering = ["startAt"]
    form = CompetitionAdminForm

    def get_queryset(self, request):
        return super(CompetitionAdmin, self).get_queryset(request)

    class Meta:
        ordering = ("")


@admin.register(Submission)
class SubmitAdmin(admin.ModelAdmin):
    list_display = ["__str__", "submitted", "late", "valid",
                    "repo", "createdOn", "submitOn", "totalActiveMembers"]
    list_filter = ["competition", "submitted", "late", "valid"]
    ordering = ["submitOn"]


@admin.register(SubmissionTopicPoint)
class TopicPointAdmin(admin.ModelAdmin):
    list_display = ["__str__", "topic", "judge", "points"]
    list_filter = ["topic"]
    ordering = ["points"]


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ["__str__", "competition", "rank", "points"]
    list_filter = ["competition", ]
    form = ResultAdminForm
    ordering = ["rank", "points"]

    class Meta:
        ordering = ("")


@admin.register(CompetitionJudge)
class JudgePanelAdmin(admin.ModelAdmin):
    list_display = ["competition", "judge"]
    list_filter = ["competition"]
    form = JudgePanelForm

    class Meta:
        ordering = ("")


@admin.register(CompetitionTopic)
class TopicRelationAdmin(admin.ModelAdmin):
    list_display = ["competition", "topic"]
    list_filter = ["topic"]

    class Meta:
        ordering = ("")

@admin.register(SubmissionParticipant)
class SubmissionParticipantAdmin(admin.ModelAdmin):
    list_display = ["submission", "profile", "confirmed"]
    list_filter = ["confirmed"]

    class Meta:
        ordering = ("")

@admin.register(ParticipantCertificate)
class ParticipantCertificateAdmin(admin.ModelAdmin):
    list_display = ["profile", "result"]
    list_filter = ["result__competition"]

    class Meta:
        ordering = ("")

@admin.register(AppreciationCertificate)
class AppreciationCertificateAdmin(admin.ModelAdmin):
    list_display = ["appreciatee", "competition"]
    list_filter = ["competition"]

    class Meta:
        ordering = ("")

@admin.register(Perk)
class PerkAdmin(admin.ModelAdmin):
    list_display = ["competition", "rank", "name"]
    list_filter = ["competition"]

    class Meta:
        ordering = ("")