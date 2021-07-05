from allauth.account.forms import SignupForm
from django import forms
from .methods import convertToFLname

class CustomSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    first_name = forms.CharField(max_length=50, label='Your Name',help_text="Your Name",widget=forms.TextInput(attrs={'placeholder': 'Your Name', 'autocomplete': 'name', 'type':'text'}))
    
    def save(self,request):
        try:
            fname, lname = convertToFLname(str(self.cleaned_data["first_name"]))
            self.cleaned_data["first_name"] = fname
            if lname:
                self.cleaned_data["last_name"] = lname
        except:
            pass
        return super(CustomSignupForm,self).save(request)        
