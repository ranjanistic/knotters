from compete.models import Competition, Submission,Result, Relation
from django.contrib import admin
from .forms import CompetitionAdminForm, ResultAdminForm



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
    list_display = ["__str__", "submitted", "repo","createdOn","submitOn","totalActiveMembers"]
    list_filter = ["competition","submitted"]
    ordering = ["submitOn"]

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ["submission", "competition", "rank"]
    list_filter = ["competition"]
    form = ResultAdminForm
    ordering = ["rank"]
    class Meta:
        ordering = ("")
    
admin.site.register(Relation)