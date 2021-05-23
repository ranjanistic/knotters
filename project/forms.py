from allauth.account.forms import SignupForm
from django import forms
from django.db.models.fields.files import ImageFieldFile


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=50, label='First Name',help_text="First Name",widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=50, label='Last Name',help_text="Last Name",widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    profile_pic = forms.ImageField(label="Profile picture")
    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.profile_pic = self.cleaned_data["profile_pic"]
        user.save()
        return user