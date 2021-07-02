from .models import Moderation
from django import forms
from main.strings import code,PROJECTS,PEOPLE,COMPETE

class ModerationAdminForm(forms.ModelForm):
    class Meta:
        model = Moderation
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        project = cleaned_data.get('project')
        profile = cleaned_data.get('profile')
        competition = cleaned_data.get('competition')
        status = cleaned_data.get('status')
        type = cleaned_data.get('type')
        moderator = cleaned_data.get('moderator')
        resolved = cleaned_data.get('resolved')

        if resolved and status == code.MODERATION:
            raise forms.ValidationError(f"resolved cannot be true while status is {code.MODERATION}, and vice versa.")

        if not resolved and status != code.MODERATION:
            raise forms.ValidationError(f"resolved cannot be false while status is not {code.MODERATION}, and vice versa.")

        if type == PROJECTS:
            if status != project.status:
                raise forms.ValidationError(f"Project status and moderation status cannot conflict.")
        
        if type == COMPETE:
            if competition.isParticipant(moderator):
                raise forms.ValidationError(f"The selected moderator is a participant in this competition.")
        
        if type == PEOPLE:
            if profile == moderator:
                raise forms.ValidationError(f"Moderation and Profile cannot be the same.")

        return cleaned_data