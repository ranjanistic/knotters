from .models import Competition, JudgeRelation, Result, Submission
from django.utils import timezone
from django import forms
from main.strings import code

class CompetitionAdminForm(forms.ModelForm):
    class Meta:
        model = Competition
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        banner = cleaned_data.get('banner')
        startAt = cleaned_data.get('startAt')
        endAt = cleaned_data.get('endAt')
        resultDeclared = cleaned_data.get('resultDeclared')
        if startAt >= endAt:
            raise forms.ValidationError(u"endAt should be greater than startAt")

        comp = None
        err = False
        try:
            comp = Competition.objects.get(banner=banner)
        except: pass
        
        if comp and comp.resultDeclared and (endAt != comp.endAt or startAt != comp.startAt):
            raise forms.ValidationError(u"endAt and startAt can\'t be changed as resultDeclared is True.")

        if resultDeclared and endAt > timezone.now():
            raise forms.ValidationError(u"resultDeclared cannot be true while endAt is still in future.")
        
        if comp and resultDeclared and not comp.moderated():
            raise forms.ValidationError(u"resultDeclared cannot be true if competition is not yet moderated.")

        return cleaned_data


class JudgePanelForm(forms.ModelForm):
    class Meta:
        model = JudgeRelation
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        comp = cleaned_data.get('competition')
        judge = cleaned_data.get('judge')

        if comp.resultDeclared:
            raise forms.ValidationError(f"Cannot assign judge as result of this competition already declared.")

        if comp.isParticipant(judge):
            raise forms.ValidationError(f"The selected judge is a participant in this competition, thus cannot be assigned.")

        if comp.isJudge(judge):
            raise forms.ValidationError(f"The selected judge is already in judge panel of this competition, thus cannot be assigned.")

        if comp.isModerator(judge):
            raise forms.ValidationError(f"The selected judge is the moderator of this competition, thus cannot be assigned.")
        
        return cleaned_data


class ResultAdminForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        comp = cleaned_data.get('competition')
        sub = cleaned_data.get('submission')
        points = cleaned_data.get('points')
        rank = cleaned_data.get('rank')

        if sub.competition != comp:
            raise forms.ValidationError(f"This submission and competition do not relate.")
        
        if rank < 1:
            raise forms.ValidationError(u"Rank cannot be less than 1")
        
        if comp.getMaxScore() < points or points < 0:
            raise forms.ValidationError(f"Points for each result in this competition should be in range 0 to {comp.getMaxScore()}")


        subcount = comp.totalValidSubmissions()
        if rank > subcount:
            raise forms.ValidationError(f"Rank cannot be greater than {subcount} for this competition.")

        duplicate = False
        
        try:
            Result.objects.get(competition=comp, rank=rank)
            duplicate = True
        except: pass

        if duplicate:
            raise forms.ValidationError(f"Rank {rank} already procured in this competition.")

        try:
            Result.objects.get(competition=comp, submission=sub)
            duplicate = True
        except: pass

        if duplicate:
            raise forms.ValidationError(u"Result for this submission is already present for this competition.")

        return cleaned_data