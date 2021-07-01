from .models import Moderation
from django import forms
from main.strings import code

class ModerationAdminForm(forms.ModelForm):
    class Meta:
        model = Moderation
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        status = cleaned_data.get('status')
        resolved = cleaned_data.get('resolved')
        retries = cleaned_data.get('retries')

        if retries < 0 or retries > 3:
            raise forms.ValidationError(f"0 <= retries <= 3")

        if resolved and status == code.MODERATION:
            raise forms.ValidationError(f"resolved cannot be true while status is {code.MODERATION}, and vice versa.")

        if not resolved and status != code.MODERATION:
            raise forms.ValidationError(f"resolved cannot be false while status is not {code.MODERATION}, and vice versa.")

        return cleaned_data