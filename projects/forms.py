from django import forms
from main.env import MAILUSER

from .models import *


class LegalDocForm(forms.ModelForm):
    content = forms.CharField(max_length=100000, help_text="The main content of document, HTML allowed.",
                              required=True, widget=forms.Textarea(attrs=dict(rows=20, cols=140, placeholder='HTML allowed')))
    contactmail = forms.CharField(max_length=100000, help_text="Query email",
                                  required=True, widget=forms.TextInput(attrs=dict(type='email', value=MAILUSER)))

    class Meta:
        model = LegalDoc
        fields = "__all__"
