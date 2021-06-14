from allauth.account.forms import SignupForm
from django import forms
from django.db.models.fields.files import ImageFieldFile


class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    first_name = forms.CharField(max_length=50, label='Your Name',help_text="Your Name",widget=forms.TextInput(attrs={'placeholder': 'Your Name', 'autocomplete': 'name', 'type':'text'}))
    
    def save(self,request):
        try:
            name = str(self.cleaned_data["first_name"]).title()
            namesequence = name.split(" ")
            self.cleaned_data["first_name"] = namesequence[0]
            del namesequence[0]
            self.cleaned_data["last_name"] = " ".join(namesequence)
        except:
            pass
        return super(CustomSignupForm,self).save(request)
        

    