from compete.models import Competition, Submission,Result
from django.contrib import admin



@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ["title","tagline","active"]
    list_filter = ["active"]
    def get_queryset(self,request):
        return super(CompetitionAdmin,self).get_queryset(request)
    class Meta:
        ordering = ("")

@admin.register(Submission)
class SubmitAdmin(admin.ModelAdmin):
    list_display = ["id", "submitted", "repo"]
    list_filter = ["submitted", "competition"]
    

admin.site.register(Result)