from compete.models import Competition, JudgePanel, Submission,Result, Relation
from django.contrib import admin
from .forms import CompetitionAdminForm, ResultAdminForm,JudgePanelForm



@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["title","tagline", "banner"]
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
    list_display = ["submission", "competition", "rank"]
    list_filter = ["competition"]
    form = ResultAdminForm
    ordering = ["rank"]
    class Meta:
        ordering = ("")

@admin.register(JudgePanel)
class JudgePanelAdmin(admin.ModelAdmin):
    list_display = ["competition", "judge"]
    list_filter = ["competition", "judge"]
    form = JudgePanelForm
    class Meta:
        ordering = ("")

admin.site.register(Relation)