from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import Profile, Relation, Setting, Topic, User


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

    list_display = ("id",  "email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2")}
         ),
    )
    search_fields = ("email", )
    ordering = ("-id", )
    filter_horizontal = ()


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "githubID", "picture"]
    list_filter = ["is_moderator"]
    def get_queryset(self, request):
        query_set = super(ProfileAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")

@admin.register(Relation)
class RelationAdmin(admin.ModelAdmin):
    list_display = ["topic", "profile"]
    list_filter = ["topic"]
    def get_queryset(self, request):
        query_set = super(RelationAdmin, self).get_queryset(request)
        return query_set

    class Meta:
        ordering = ("")

admin.site.register(Setting)
admin.site.register(Topic)