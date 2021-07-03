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

        if not moderator.is_moderator:
            raise forms.ValidationError(f"The selected moderator is not a valid moderator.")

        if resolved and status == code.MODERATION:
            raise forms.ValidationError(f"resolved cannot be true while status is {code.MODERATION}, and vice versa.")

        if not resolved and status != code.MODERATION:
            raise forms.ValidationError(f"resolved cannot be false while status is not {code.MODERATION}, and vice versa.")

        if type == PROJECTS:
            if profile or competition:
                raise forms.ValidationError(f"Cannot accept profile or competition for moderation type {type}.")

            if status != project.status:
                raise forms.ValidationError(f"Project status and moderation status cannot conflict.")
        
        if type == COMPETE:
            if profile or project:
                raise forms.ValidationError(f"Cannot accept profile or project for moderation type {type}.")

            if status == code.REJECTED:
                raise forms.ValidationError(f"Cannot set status as {code.REJECTED} for moderation type {type}.")

            if competition.isParticipant(moderator):
                raise forms.ValidationError(f"The selected moderator is a participant in this competition, thus cannot be assigned.")

            if competition.isJudge(moderator):
                raise forms.ValidationError(f"The selected moderator is in judge panel of this competition, thus cannot be assigned.")

            if not resolved and competition.resultDeclared:
                raise forms.ValidationError(f"Resolved cannot be false as competition results have been declared.")

        
        if type == PEOPLE:
            if competition or project:
                raise forms.ValidationError(f"Cannot accept competition or project for moderation type {type}.")

            if profile == moderator:
                raise forms.ValidationError(f"Moderator and Profile cannot be the same.")

        return cleaned_data