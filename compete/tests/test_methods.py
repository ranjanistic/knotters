from main.env import BOTMAIL
from compete.models import SubmissionTopicPoint
from uuid import uuid4
from datetime import timedelta
from django.utils import timezone
from main.strings import Code
from django.test import TestCase, tag
from people.models import Profile, Topic
from moderation.models import Moderation
from moderation.methods import assignModeratorToObject
from people.tests.utils import getTestEmail, getTestName, getTestPassword
from main.methods import getDeepFilePaths
from main.tests.utils import getRandomStr
from people.tests.utils import getTestEmail, getTestName, getTestPassword, getTestUsersInst, getTestTopicsInst
from .utils import getCompTitle, getCompPerks, getCompBanner, getSubmissionRepos
from compete.apps import APPNAME
from compete.methods import *
from random import randint


@tag(Code.Test.METHOD, APPNAME)
class CompeteMethodsTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        self.mguser = User.objects.create_user(
            email=getTestEmail(), password=getTestPassword(), first_name=getTestName())
        self.mgprofile = Profile.objects.filter(
            user=self.mguser).update(is_manager=True)
        self.comp = Competition.objects.create(title=getCompTitle(), creator=self.mguser.profile, startAt=timezone.now(
        ), endAt=timezone.now()+timedelta(days=3), eachTopicMaxPoint=30)
        self.user = User.objects.create_user(email=getTestEmail(
        ), password=getTestPassword(), first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.topic = Topic.objects.bulk_create(getTestTopicsInst())[0]
        self.comp.topics.add(self.topic)
        users = User.objects.bulk_create(getTestUsersInst(6))
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
        self.moderator = Profile.objects.filter(user__in=users)[5:6][0]
        self.moderator.is_moderator=True
        self.moderator.save()
        self.subm = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm.members.add(self.user)
        self.subm2 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm2.members.add(self.user2)
        self.subm3 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm3.members.add(self.user3)
        self.subm4 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm4.members.add(self.user4)
        self.subm5 = Submission.objects.create(
            competition=self.comp, repo=getSubmissionRepos()[0], submitted=True, submitOn=now)
        self.subm5.members.add(self.user5)
        SubmissionParticipant.objects.filter(confirmed=False).update(confirmed=True)
        assignModeratorToObject(APPNAME,self.comp,self.moderator,self.comp.title)
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
        Moderation.objects.filter(type=APPNAME,competition=self.comp,moderator=self.moderator).update(resolved=True)
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
        self.comp.endAt = timezone.now()
        self.comp.save()
        self.comp.declareResults()
        
        cert = generateCertificate(certname=f'{self.comp.get_id}-{self.user.getID()}',
            certID=uuid4().hex,
            username=self.user.getName(),
            compname=self.comp.title,
            abouttext=f"from {self.comp.startAt.strftime('%B')} {self.comp.startAt.day}, {self.comp.startAt.year} to {self.comp.endAt.strftime('%B')} {self.comp.endAt.day}, {self.comp.endAt.year}"
        )
        self.assertTrue(cert.endswith('.pdf'))
        
        cert = generateModCertificate(
            competition=self.comp,
            certID=uuid4().hex,
        )
        self.assertTrue(cert.endswith('.pdf'))

        cert = generateJudgeCertificate(
            judge=self.judge,
            competition=self.comp,
            certID=uuid4().hex,
        )
        self.assertTrue(cert.endswith('.pdf'))

        result = Result.objects.get(submission=self.subm2,competition=self.comp)
        cert = generateParticipantCertificate(
            profile=self.user2,
            result=result,
            certID=uuid4().hex,
        )
        self.assertTrue(cert.endswith('.pdf'))

