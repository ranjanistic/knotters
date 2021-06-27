from compete.models import Competition, Submission,Result, Relation
from django.contrib import admin
from .forms import CompetitionAdminForm



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
    list_display = ["id", "submitted", "repo"]
    list_filter = ["submitted", "competition"]
    

admin.site.register(Result)
admin.site.register(Relation)