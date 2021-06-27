from .models import Competition
from django.utils import timezone
from django import forms

class CompetitionAdminForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        startAt = cleaned_data.get('startAt')
        endAt = cleaned_data.get('endAt')
        resultDeclared = cleaned_data.get('resultDeclared')
        if startAt >= endAt:
            raise forms.ValidationError(u"\'endAt\' should be greater than \'startAt\'")
        if resultDeclared and endAt > timezone.now():
            raise forms.ValidationError(u"\'resultDeclared\' cannot be true while \'endAt\' is still in future.")
        return cleaned_data