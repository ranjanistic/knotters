from allauth.account.forms import SignupForm
from django import forms
from django.db.models.fields.files import ImageFieldFile


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=50, label='Your Name',help_text="Your Name",widget=forms.TextInput(attrs={'placeholder': 'Your Name', 'autocomplete': 'name', 'type':'text'}))
    def signup(self, request, user):
        namesequence = str(self.cleaned_data['first_name']).split(" ")
        print(namesequence)
        user.first_name = namesequence[0]
        del namesequence[0]
        print(namesequence)
        if len(namesequence) > 0:
            user.last_name = "".join(namesequence)
            print(user.last_name)
        user.save()
        return user