from compete.models import SubmissionTopicPoint
from datetime import timedelta
from django.utils import timezone
from main.strings import Code
from django.test import TestCase, tag
from people.models import Profile, Topic
from people.tests.utils import getTestEmail, getTestName, getTestPassword
from main.tests.utils import getRandomStr
from people.tests.utils import getTestEmail, getTestName, getTestPassword, getTestUsersInst, getTestTopicsInst
from .utils import getCompTitle, getCompPerks, getCompBanner, getSubmissionRepos
from compete.methods import *
from random import randint


@tag(Code.Test.METHOD, APPNAME)
class CompeteMethodsTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.mguser = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.mgprofile = Profile.objects.filter(
            user=self.mguser).update(is_manager=True)
        self.comp = Competition.objects.create(title=getCompTitle(), creator=self.mguser.profile, startAt=timezone.now(), endAt=timezone.now()+timedelta(days=3), eachTopicMaxPoint=30)
        self.user = User.objects.create_user(email=getTestEmail(
        ), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.topic = Topic.objects.bulk_create(getTestTopicsInst())[0]
        self.comp.topics.add(self.topic)
        users = User.objects.bulk_create(getTestUsersInst(5))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        self.judge = Profile.objects.filter(user__in=users)[0:1][0]
        self.comp.judges.add(self.judge)
        now = timezone.now()
        self.user = Profile.objects.filter(user__in=users)[1:2][0]
        self.user2 = Profile.objects.filter(user__in=users)[2:3][0]
        self.user3 = Profile.objects.filter(user__in=users)[2:3][0]
        self.user4 = Profile.objects.filter(user__in=users)[3:4][0]
        self.user5 = Profile.objects.filter(user__in=users)[4:5][0]
        self.subm = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm.members.add(self.user)
        self.subm2 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm2.members.add(self.user)
        self.subm3 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm3.members.add(self.user)
        self.subm4 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm4.members.add(self.user)
        self.subm5 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm5.members.add(self.user)
        SubmissionParticipant.objects.filter(submission__in=[
                                             self.subm2, self.subm3, self.subm4, self.subm4, self.subm5]).update(confirmed=True)
        self.submTopicPoint = SubmissionTopicPoint.objects.create(
            submission=self.subm, judge=self.judge, topic=self.topic, points=randint(0, self.comp.eachTopicMaxPoint))
        self.submTopicPoint2 = SubmissionTopicPoint.objects.create(
            submission=self.subm2, judge=self.judge, topic=self.topic, points=randint(0, self.comp.eachTopicMaxPoint))
        self.submTopicPoint3 = SubmissionTopicPoint.objects.create(
            submission=self.subm3, judge=self.judge, topic=self.topic, points=randint(0, self.comp.eachTopicMaxPoint))
        self.submTopicPoint4 = SubmissionTopicPoint.objects.create(
            submission=self.subm4, judge=self.judge, topic=self.topic, points=randint(0, self.comp.eachTopicMaxPoint))
        self.submTopicPoint5 = SubmissionTopicPoint.objects.create(
            submission=self.subm5, judge=self.judge, topic=self.topic, points=randint(0, self.comp.eachTopicMaxPoint))
        return super().setUpTestData()

    def test_competition_section_data(self):
        self.assertIsNone(getCompetitionSectionData(
            getRandomStr(), self.comp, self.user))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.OVERVIEW, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.TASK, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.GUIDELINES, self.comp, self.user), dict(compete=self.comp))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.SUBMISSION, self.comp, self.user), dict(compete=self.comp, submission=None))
        self.assertDictEqual(getCompetitionSectionData(
            Compete.RESULT, self.comp, self.user), dict(compete=self.comp, results=None))

    def test_certificate_generator(self):
        self.comp.declareResults()
        results = Result.objects.filter(competition=self.comp)
        AllotParticipantCertificates(results, self.comp)
        self.assertEqual(ParticipantCertificate.objects.filter(
            result__competition=self.comp).count(), self.comp.totalValidSubmissionParticipants())
