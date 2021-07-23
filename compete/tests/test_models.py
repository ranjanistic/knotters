from django.db.models import Q
from django.test import TestCase, tag
from main.strings import Code
from people.models import User
from people.tests.utils import getTestUsersInst, getTestTopicsInst
from compete.models import *
from .utils import TEST_COMP_TITLE, getSubmissionRepos


@tag(Code.Test.MODEL, APPNAME)
class CompetitionTest(TestCase):
    def test_comp_creation_pass(self):
        comp = Competition.objects.create(title=TEST_COMP_TITLE)
        self.assertIsNotNone(comp.title)


@tag(Code.Test.MODEL, APPNAME)
class CompetitionM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        users = User.objects.bulk_create(getTestUsersInst(3))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))

    def test_comp_assign_judges(self):
        for judge in self.judges:
            self.comp.judges.add(judge)
        count = CompetitionJudge.objects.filter(competition=self.comp).count()
        self.assertEqual(count, len(self.judges))

    def test_comp_unassign_judges(self):
        CompetitionJudge.objects.filter(competition=self.comp).delete()
        comp = Competition.objects.get(id=self.comp.getID())
        self.assertEqual(comp.judges.count(), 0)

    def test_comp_assign_topics(self):
        for topic in self.topics:
            self.comp.topics.add(topic)
        count = CompetitionTopic.objects.filter(competition=self.comp).count()
        self.assertEqual(count, len(self.topics))

    def test_comp_unassign_topics(self):
        CompetitionTopic.objects.filter(competition=self.comp).delete()
        comp = Competition.objects.get(id=self.comp.getID())
        self.assertEqual(comp.topics.count(), 0)


@tag(Code.Test.MODEL, APPNAME)
class SubmissionTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        users = User.objects.bulk_create(getTestUsersInst(54))
        profiles = []
        for user in users:
            profiles.append(Profile(
                user=user
            ))
        Profile.objects.bulk_create(profiles)
        cls.judges = Profile.objects.filter(user__in=users)[0:3]
        for judge in cls.judges:
            cls.comp.judges.add(judge)
        cls.users = Profile.objects.filter(user__in=users)[3:54]

    def test_submission_creation(self):
        submissions = []
        i = 0
        for repo in getSubmissionRepos(len(self.users)):
            submissions.append(Submission(
                competition=self.comp,
                repo=repo
            ))
            i += 1
        subs = Submission.objects.bulk_create(submissions)
        s = 0
        for sub in Submission.objects.filter(competition=self.comp):
            sub.members.add(self.users[s])
            s+=1

        self.assertEqual(len(subs),len(self.users))
        count = SubmissionParticipant.objects.filter(submission__competition=self.comp, profile__in=self.judges).count()
        self.assertEqual(count,0)
        count = Submission.objects.filter(competition=self.comp,submitted=False, valid=False).count()
        self.assertEqual(count,0)
        count = Submission.objects.filter(competition=self.comp,submitted=True).count()
        self.assertEqual(count,0)
        count = Submission.objects.filter(competition=self.comp,late=True).count()
        self.assertEqual(count,0)
        count = Submission.objects.filter(competition=self.comp,submitted=False,late=True).count()
        self.assertEqual(count,0)

    def test_submission_invalidation(self):
        submissions = []
        i = 0
        print(len(self.users),self.users.count())
        for repo in getSubmissionRepos(len(self.users)):
            submissions.append(Submission(
                competition=self.comp,
                repo=repo,
            ))
            i += 1
        subs = Submission.objects.bulk_create(submissions)
        s = 0
        for sub in Submission.objects.filter(competition=self.comp):
            sub.members.add(self.users[s])
            s+=1
        Submission.objects.filter(competition=self.comp, repo__endswith='0').update(valid=False)
        comp = Competition.objects.get(id=self.comp.getID())
        self.assertEquals(comp.totalValidSubmissions(),Submission.objects.filter(Q(competition=self.comp),~Q(repo__endswith='0')).count())


@tag(Code.Test.MODEL, APPNAME)
class SubmissionM2MTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.comp = Competition.objects.create(title=TEST_COMP_TITLE)
        cls.topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        users = User.objects.bulk_create(getTestUsersInst(54))
        cls.judges = Profile.objects.filter(user__in=users)[0:3]
        for judge in cls.judges:
            cls.comp.judges.add(judge)
        cls.users = Profile.objects.filter(user__in=users)[3:54]
        submissions = []
        i = 0
        for repo in getSubmissionRepos(len(cls.users)):
            submissions.append(Submission(
                competition=cls.comp,
                repo=repo
            ))
            i += 1
        cls.subs = Submission.objects.bulk_create(submissions)
        s = 0
        for sub in Submission.objects.filter(competition=cls.comp):
            sub.members.add(cls.users[s])
            s+=1
    
    def test_submission_members(self):
        s = 0
        for sub in self.subs:
            sub.members.remove(self.users[s+3])
            self.assertEqual(SubmissionParticipant.objects.filter(submission=sub, profile=self.users[s+3]).count(),0)

