from compete.models import Competition, JudgeRelation, Submission,Result, ParticipantRelation, TopicRelation
from django.contrib import admin
from .forms import CompetitionAdminForm, ResultAdminForm,JudgePanelForm



@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["title","tagline","isActive","startAt","endAt", "banner"]
    list_filter = ["resultDeclared", "eachTopicMaxPoint"]
    ordering = ["startAt"]
    form = CompetitionAdminForm
    def get_queryset(self,request):
        return super(CompetitionAdmin,self).get_queryset(request)
    class Meta:
        ordering = ("")

@admin.register(Submission)
class SubmitAdmin(admin.ModelAdmin):
    list_display = ["__str__", "submitted", "late", "repo","createdOn","submitOn","totalActiveMembers"]
    list_filter = ["competition","submitted", "late"]
    ordering = ["submitOn"]

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ["__str__", "competition", "rank"]
    list_filter = ["competition"]
    form = ResultAdminForm
    ordering = ["rank"]
    class Meta:
        ordering = ("")

@admin.register(JudgeRelation)
class JudgePanelAdmin(admin.ModelAdmin):
    list_display = ["competition", "judge"]
    list_filter = ["competition", "judge"]
    form = JudgePanelForm
    class Meta:
        ordering = ("")

@admin.register(TopicRelation)
class TopicRelationAdmin(admin.ModelAdmin):
    list_display = ["competition", "topic"]
    list_filter = ["topic"]
    class Meta:
        ordering = ("")

admin.site.register(ParticipantRelation)