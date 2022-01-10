from django.contrib import admin
from .models import *



admin.site.register(Country)
admin.site.register(Address)
admin.site.register(PhoneNumber)

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ["name", "country"]
    list_filter = ["country"]

    def get_queryset(self, request):
        query_set = super(StateAdmin, self).get_queryset(request)
        return query_set