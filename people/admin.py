from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.models import Group

from .models import *


class UserCreationForm(forms.ModelForm):
    email = forms.CharField(label="Email", widget=forms.EmailInput)
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = "__all__"

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = "__all__"

    def clean_password(self):
        return self.initial["password"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = ("getID",  "email", "getName", "date_joined", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
        ("Account state", {"fields": ("is_active","is_admin","is_staff")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2")}
         ),
    )
    search_fields = ("email", "first_name", "last_name")
    ordering = ("-date_joined", "last_login")
    search_fields = ['email','first_name', 'last_name']
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["getName", "user", "githubID", "picture"]
    list_filter = ["is_moderator", "to_be_zombie", "is_zombie", "is_active"]
    ordering = ['-createdOn']
    search_fields = ['nickname', 'githubID']
    autocomplete_fields = ['user', 'successor']

    def get_queryset(self, request):
        query_set = super(ProfileAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


@admin.register(ProfileTopic)
class PTAdmin(admin.ModelAdmin):
    list_display = ["topic", "profile"]
    list_filter = ["topic"]
    autocomplete_fields = ['profile', 'topic']

    def get_queryset(self, request):
        query_set = super(RelationAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")


admin.site.register(ProfileSetting)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    search_fields = ['name']

admin.site.register(BlockedUser)
admin.site.register(ReportedUser)

@admin.register(DisplayMentor)
class DisplayMentorAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']

@admin.register(CoreContributor)
class CoreContributorAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']


@admin.register(CoreMember)
class CoreMemberAdmin(admin.ModelAdmin):
    autocomplete_fields = ['profile']

admin.site.register(GHMarketPurchase)
