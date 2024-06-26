from compete.models import Competition
from django import forms
from django.db.models import Q
from main.strings import COMPETE, PEOPLE, PROJECTS, Code
from people.models import Profile
from projects.models import Project

from .models import Moderation


class ModerationAdminForm(forms.ModelForm):
    moderator = forms.ModelChoiceField(queryset=Profile.objects.filter(
        is_zombie=False, to_be_zombie=False, is_active=True, is_moderator=True, suspended=False))
    project = forms.ModelChoiceField(queryset=Project.objects.filter(
        ~Q(status=Code.APPROVED), trashed=False), required=False)
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(resultDeclared=False), required=False)

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
            raise forms.ValidationError(
                f"The selected moderator is not a valid moderator.")

        if resolved and status == Code.MODERATION:
            raise forms.ValidationError(
                f"resolved cannot be true while status is {Code.MODERATION}, and vice versa.")

        if not resolved and status != Code.MODERATION:
            raise forms.ValidationError(
                f"resolved cannot be false while status is not {Code.MODERATION}, and vice versa.")

        if type == PROJECTS:
            if profile or competition:
                raise forms.ValidationError(
                    f"Cannot accept profile or competition for moderation type {type}.")

            if status != project.status:
                raise forms.ValidationError(
                    f"Project status and moderation status cannot conflict.")

            if moderator == project.creator:
                raise forms.ValidationError(
                    f"Project creator cannot be its moderator.")

        if type == COMPETE:
            if profile or project:
                raise forms.ValidationError(
                    f"Cannot accept profile or project for moderation type {type}.")

            if status == Code.REJECTED:
                raise forms.ValidationError(
                    f"Cannot set status as {Code.REJECTED} for moderation type {type}.")

            if competition.isParticipant(moderator):
                raise forms.ValidationError(
                    f"The selected moderator is a participant in this competition, thus cannot be assigned.")

            if competition.isJudge(moderator):
                raise forms.ValidationError(
                    f"The selected moderator is in judge panel of this competition, thus cannot be assigned.")

            if not resolved and competition.resultDeclared:
                raise forms.ValidationError(
                    f"Resolved cannot be false as competition results have been declared.")

        if type == PEOPLE:
            if competition or project:
                raise forms.ValidationError(
                    f"Cannot accept competition or project for moderation type {type}.")

            if profile == moderator:
                raise forms.ValidationError(
                    f"Moderator and Profile cannot be the same.")

        return cleaned_data
