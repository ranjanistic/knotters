from django.utils import timezone
from django import forms
from people.models import Profile
from .models import Competition, CompetitionJudge, Result, Submission, SubmissionParticipant, SubmissionTopicPoint


class CompetitionAdminForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea, max_length=20000,
                                  help_text="This will be shown in the overview, along with perks, only after the competition as started.")
    taskSummary = forms.CharField(
        widget=forms.Textarea, max_length=50000, help_text="The summary of task (HTML allowed).")
    taskDetail = forms.CharField(
        widget=forms.Textarea, max_length=100000, help_text="The details of task (HTML allowed).")
    taskSample = forms.CharField(widget=forms.Textarea, max_length=10000,
                                 help_text="The task sample submission (HTML allowed).")

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
            raise forms.ValidationError(
                u"endAt should be greater than startAt")

        comp = None
        err = False
        try:
            comp = Competition.objects.get(banner=banner)
        except:
            pass

        if comp and comp.resultDeclared and (endAt != comp.endAt or startAt != comp.startAt):
            raise forms.ValidationError(
                u"endAt and startAt can\'t be changed as resultDeclared is True.")

        if resultDeclared and endAt > timezone.now():
            raise forms.ValidationError(
                u"resultDeclared cannot be true while endAt is still in future.")

        if comp and resultDeclared and not comp.moderated():
            raise forms.ValidationError(
                u"resultDeclared cannot be true if competition is not yet moderated.")

        return cleaned_data


class JudgePanelForm(forms.ModelForm):
    competition = forms.ModelChoiceField(
        queryset=Competition.objects.filter(resultDeclared=False))
    judge = forms.ModelChoiceField(queryset=Profile.objects.filter(
        is_zombie=False, to_be_zombie=False, is_active=True))

    class Meta:
        model = CompetitionJudge
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        comp = cleaned_data.get('competition')
        judge = cleaned_data.get('judge')

        if comp.resultDeclared:
            raise forms.ValidationError(
                f"Cannot assign judge as result of this competition already declared.")

        if comp.isParticipant(judge):
            raise forms.ValidationError(
                f"The selected judge is a participant in this competition, thus cannot be assigned.")

        if comp.isJudge(judge):
            raise forms.ValidationError(
                f"The selected judge is already in judge panel of this competition, thus cannot be assigned.")

        if comp.isModerator(judge):
            raise forms.ValidationError(
                f"The selected judge is the moderator of this competition, thus cannot be assigned.")

        return cleaned_data

class SubmissionParticipantForm(forms.ModelForm):
    submission = forms.ModelChoiceField(queryset=Submission.objects.filter(competition__resultDeclared=False, valid=True))
    profile = forms.ModelChoiceField(queryset=Profile.objects.filter(is_zombie=False, to_be_zombie=False, is_active=True))
    
    class Meta:
        model = SubmissionParticipant
        fields = "__all__"


class SubmissionTopicPointForm(forms.ModelForm):
    submission = forms.ModelChoiceField(queryset=Submission.objects.filter(
        competition__resultDeclared=False, valid=True, competition__endAt__lt=timezone.now()))
    judge = forms.ModelChoiceField(queryset=Profile.objects.filter(
        is_zombie=False, to_be_zombie=False, is_active=True))

    class Meta:
        model = SubmissionTopicPoint
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        sub = cleaned_data.get('submission')
        topic = cleaned_data.get('topic')
        points = cleaned_data.get('points')
        judge = cleaned_data.get('judge')

        if sub and sub.competition.resultDeclared:
            raise forms.ValidationError(
                f"Selected submission's result has already been declared")
        if topic and topic not in sub.competition.getTopics():
            raise forms.ValidationError(
                f"Selected topic is not related with the submission")
        if sub and judge and not sub.competition.isJudge(judge):
            raise forms.ValidationError(
                f"The selected judge is not assigned for this submission.")
        if points and sub and (points < 0 or points > sub.competition.eachTopicMaxPoint):
            raise forms.ValidationError(
                f"Point should be >=0 and <={sub.competition.eachTopicMaxPoint}")

        if sub and (sub.pointedTopicsByJudge(judge) == sub.competition.totalTopics()):
            raise forms.ValidationError(
                f"All topic points of this submission by selected judge already assigned.")

        return cleaned_data


class ResultAdminForm(forms.ModelForm):
    
    competition = forms.ModelChoiceField(queryset=Competition.objects.filter(
        resultDeclared=False, endAt__lt=timezone.now()))
    submission = forms.ModelChoiceField(queryset=Submission.objects.filter(
        competition__resultDeclared=False, valid=True, competition__endAt__lt=timezone.now()))

    class Meta:
        model = Result
        fields = "__all__"

    def clean(self):
        cleaned_data = self.cleaned_data
        comp = cleaned_data.get('competition')
        sub = cleaned_data.get('submission')
        points = cleaned_data.get('points')
        rank = cleaned_data.get('rank')

        if sub and sub.competition != comp:
            raise forms.ValidationError(
                f"This submission and competition do not relate.")

        if rank and rank < 1:
            raise forms.ValidationError(u"Rank cannot be less than 1")

        if comp and (comp.getMaxScore() < points or points < 0):
            raise forms.ValidationError(
                f"Points for each result in this competition should be in range 0 to {comp.getMaxScore()}")

        subcount = None if not comp else comp.totalValidSubmissions()
        if subcount and (rank > subcount):
            raise forms.ValidationError(
                f"Rank cannot be greater than {subcount} for this competition.")

        duplicate = False

        try:
            Result.objects.get(competition=comp, rank=rank)
            duplicate = True
        except:
            pass

        if duplicate:
            raise forms.ValidationError(
                f"Rank {rank} already procured in this competition.")

        try:
            Result.objects.get(competition=comp, submission=sub)
            duplicate = True
        except:
            pass

        if duplicate:
            raise forms.ValidationError(
                u"Result for this submission is already present for this competition.")

        return cleaned_data
