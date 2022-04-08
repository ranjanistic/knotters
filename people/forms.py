from allauth.account.forms import SignupForm
from django.utils.translation import gettext_lazy as _
from django import forms

from .methods import convertToFLname


class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=70, label=_('Your Name'), help_text=_('Your Name'), widget=forms.TextInput(
        attrs={'placeholder': _('Your Name'), 'autocomplete': 'name', 'type': 'text', 'class': 'required-field'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def save(self, request):
        try:
            fname, lname = convertToFLname(
                str(self.cleaned_data["first_name"]))
            self.cleaned_data["first_name"] = fname.replace(
                'https://', '_').replace('http://', '_')
            if lname:
                self.cleaned_data["last_name"] = lname.replace(
                    'https://', '_').replace('http://', '_')
        except:
            pass
        return super(CustomSignupForm, self).save(request)
