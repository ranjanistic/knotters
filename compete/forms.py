from .models import Competition, Result, Submission
from django.utils import timezone
from django import forms

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
            raise forms.ValidationError(u"\'endAt\' should be greater than \'startAt\'")
        err = False
        try:
            comp = Competition.objects.get(banner=banner)
            if resultDeclared and (endAt != comp.endAt or startAt != comp.startAt):
                err = True
        except: pass
        if err:
            raise forms.ValidationError(u"endAt and startAt can\'t be changed as resultDeclared is True.")
        if resultDeclared and endAt > timezone.now():
            raise forms.ValidationError(u"\'resultDeclared\' cannot be true while \'endAt\' is still in future.")
        return cleaned_data

class ResultAdminForm(forms.ModelForm):
    class Meta:
        model = Result
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        comp = cleaned_data.get('competition')
        sub = cleaned_data.get('submission')
        rank = cleaned_data.get('rank')

        if rank < 1:
            raise forms.ValidationError(u"Rank cannot be less than 1")
        
        unrelated = True
        try:
            Submission.objects.get(id=sub.id,competition=comp)
            unrelated = False
        except: pass

        if unrelated:
            raise forms.ValidationError(f"This submission and competition do not relate.")

        subcount = Submission.objects.filter(competition=comp).count()

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