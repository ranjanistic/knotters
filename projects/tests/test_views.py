import json
from django.http.response import HttpResponseNotFound, HttpResponseRedirect
from django.test import TestCase, Client, tag
from django.db.models import QuerySet
from django.http import HttpResponse
from main.strings import Code, url, template, Message
from main.tests.utils import getRandomStr
from people.models import Profile, Topic, User
from people.tests.utils import getTestEmail, getTestGHID, getTestName, getTestPassword, getTestTopicsInst
from projects.models import Project, License, Category, Tag, defaultImagePath
from moderation.models import Moderation
from projects.apps import APPNAME
from .utils import getProjDesc, getProjRepo, getTestTags, getTestTagsInst, root, getLicName, getLicDesc, getProjName, getProjCategory


@tag(Code.Test.VIEW, APPNAME)
class TestViews(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.client = Client()
        self.license = License.objects.create(
            name=getLicName(), description=getLicDesc())
        self.email = getTestEmail()
        self.ghID = getTestGHID()
        self.password = getTestPassword()
        self.user = User.objects.create_user(
            email=self.email, password=self.password, first_name=getTestName())
        self.profile = Profile.objects.get(user=self.user)
        self.moduser = User.objects.create_user(
            email=getTestEmail(), password=self.password, first_name=getTestName())
        self.modprofile = Profile.objects.get(user=self.moduser)
        self.modprofile.is_moderator = True
        self.modprofile.save()
        return super().setUpTestData()

    def setUp(self) -> None:
        self.client = Client()

    def test_index(self):
        resp = self.client.get(follow=True, path=root(''))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)

    def test_allLicenses(self):
        resp = self.client.get(
            follow=True, path=root(url.projects.ALLLICENSES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['licenses'], QuerySet)
        self.assertNotIsInstance(resp.context['custom'], QuerySet)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.license_index)

    def test_license(self):
        resp = self.client.get(follow=True, path=root(
            url.projects.license(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        resp = self.client.get(follow=True, path=root(
            url.projects.license(self.license.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['license'], License)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.license_index)
        self.assertTemplateUsed(resp, template.projects.license_lic)

    def test_create(self):
        resp = self.client.get(path=root(url.projects.CREATE))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)
        resp = self.client.get(follow=True, path=root(url.projects.CREATE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.get(follow=True, path=root(url.projects.CREATE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(resp.context['tags'], list)
        self.assertIsInstance(resp.context['categories'], QuerySet)
        self.assertIsInstance(resp.context['licenses'], QuerySet)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.create)

    def test_validateField(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.createValidField(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.ERROR_OCCURRED))
        reponame = getRandomStr()
        resp = self.client.post(follow=True, path=root(url.projects.createValidField('reponame')), data={
            'reponame': reponame
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.Custom.already_exists(reponame)))

        resp = self.client.post(follow=True, path=root(url.projects.createValidField('reponame')), data={
            'reponame': getProjRepo()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.OK))

    def test_licenses(self):
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.LICENSES))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json.loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)

    def test_addLicense(self):
        resp = self.client.post(path=root(url.projects.ADDLICENSE))
        self.assertEqual(resp.status_code, HttpResponseRedirect.status_code)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(
            follow=True, path=root(url.projects.ADDLICENSE))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(resp.content.decode(
            Code.UTF_8)), dict(code=Code.NO, error=Message.INVALID_LIC_DATA))

        licname = getLicName()
        resp = self.client.post(follow=True, path=root(url.projects.ADDLICENSE), data={
            "name": licname,
            "description": getLicDesc(),
            "content": getRandomStr(),
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        license = License.objects.get(name=licname, creator=self.profile)
        self.assertDictEqual(json.loads(resp.content.decode(Code.UTF_8)), dict(code=Code.OK,
                             license=dict(id=license.getID(), name=license.name, description=license.description)))

    def test_submitProject(self):
        resp = self.client.post(follow=True, path=root(url.projects.SUBMIT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.SUBMIT))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.create)
        reponame = getProjRepo()
        categoryname = getProjCategory()
        data = {
            "projectname": getProjName(),
            "projectabout": getRandomStr(),
            "projectcategory": categoryname,
            "reponame": reponame,
            "description": getProjDesc(),
            "license": self.license.getID(),
            "tags": ",".join(getTestTags()),
        }
        resp = self.client.post(follow=True, path=root(
            url.projects.SUBMIT), data=data)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.create)

        data["acceptterms"] = True
        resp = self.client.post(follow=True, path=root(
            url.projects.SUBMIT), data=data)
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.moderation.index)
        self.assertTemplateUsed(resp, template.moderation.projects)
        project = Project.objects.get(
            reponame=reponame, status=Code.MODERATION)
        category = Category.objects.get(name=categoryname)
        self.assertTrue(project.acceptedTerms)
        self.assertEqual(project.creator, self.profile)
        self.assertEqual(project.moderator, self.modprofile)
        self.assertEqual(project.category, category)
        self.assertEqual(str(project.image), defaultImagePath())
        self.assertIsNone(project.approvedOn)

    def test_trashProject(self):
        project = Project.objects.create(
            name=getProjName(), creator=self.profile, reponame=getProjRepo())
        resp = self.client.post(follow=True, path=root(
            url.projects.trash(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.trash(project.getID())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)
        project.status = Code.REJECTED
        project.save()
        resp = self.client.post(follow=True, path=root(
            url.projects.trash(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertIsInstance(Project.objects.get(
            id=project.id, trashed=True), Project)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.people.index)
        self.assertTemplateUsed(resp, template.people.profile)

    def test_profile(self):
        self.client.login(email=self.email, password=self.password)
        reponame = getProjRepo()
        resp = self.client.post(follow=True, path=root(url.projects.SUBMIT), data={
            "projectname": getProjName(),
            "projectabout": getRandomStr(),
            "reponame": reponame,
            "projectcategory": getProjCategory(),
            "description": getProjDesc(),
            "license": self.license.getID(),
            "tags": ",".join(getTestTags()),
            "acceptterms": True
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.moderation.projects)

        resp = self.client.get(follow=True, path=root(
            url.projects.profile(getRandomStr())))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        project = Project.objects.get(reponame=reponame)

        self.client.logout()
        resp = self.client.get(follow=True, path=root(
            url.projects.profile(project.reponame)))
        self.assertEqual(resp.status_code, HttpResponseNotFound.status_code)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.get(follow=True, path=root(
            url.projects.profile(project.reponame)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.moderation.index)
        self.assertTemplateUsed(resp, template.moderation.projects)

        mod = Moderation.objects.get(
            type=APPNAME, project=project, resolved=False)
        self.assertTrue(mod.approve())
        resp = self.client.get(follow=True, path=root(
            url.projects.profile(project.reponame)))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.profile)
        self.assertTrue(resp.context['iscreator'])
        self.assertFalse(resp.context['ismoderator'])
        self.assertEqual(resp.context['project'], project)

    def test_editProfile(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), status=Code.APPROVED)
        resp = self.client.post(follow=True, path=root(url.projects.profileEdit(
            project.getID(), 'pallete')))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.profileEdit(project.getID(), 'pallete')), data={
            'projectname': getProjName(),
            'projectabout': getRandomStr()
        })
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        newproj = Project.objects.get(id=project.id)
        self.assertNotEqual(project.name, newproj.name)
        self.assertTemplateUsed(resp, template.index)
        self.assertTemplateUsed(resp, template.projects.index)
        self.assertTemplateUsed(resp, template.projects.profile)

    def test_topicsSearch(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), status=Code.APPROVED)

        resp = self.client.post(follow=True, path=root(
            url.projects.topicsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.topicsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = self.client.post(follow=True, path=root(url.projects.topicsSearch(project.getID())), data={
                                'query': getRandomStr()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json.loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)

    def test_topicsUpdate(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), status=Code.APPROVED)
        resp = self.client.post(follow=True, path=root(url.projects.topicsUpdate(project.getID())), data={
                                'addtopicIDs': str()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        topics = Topic.objects.bulk_create(getTestTopicsInst(4))
        addTopicIDs = ''
        for top in topics:
            addTopicIDs = f"{addTopicIDs},{top.getID()}"
        resp = self.client.post(follow=True, path=root(url.projects.topicsUpdate(project.getID())), data={
                                'addtopicIDs': addTopicIDs})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.profile)
        self.assertEqual(project.totalTopics(), 4)

    def test_tagsSearch(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), status=Code.APPROVED)

        resp = self.client.post(follow=True, path=root(
            url.projects.tagsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)

        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(
            url.projects.tagsSearch(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertDictEqual(json.loads(
            resp.content.decode(Code.UTF_8)), dict(code=Code.NO))

        resp = self.client.post(follow=True, path=root(url.projects.tagsSearch(project.getID())), data={
                                'query': getRandomStr()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertEqual(json.loads(
            resp.content.decode(Code.UTF_8))['code'], Code.OK)

    def test_tagsUpdate(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), status=Code.APPROVED)
        resp = self.client.post(follow=True, path=root(url.projects.tagsUpdate(project.getID())), data={
                                'addtagIDs': str()})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.auth.login)
        tags = Tag.objects.bulk_create(getTestTagsInst(4))
        addTagIDs = ''
        for tag in tags:
            addTagIDs = f"{addTagIDs},{tag.getID()}"
        self.client.login(email=self.email, password=self.password)
        resp = self.client.post(follow=True, path=root(url.projects.tagsUpdate(project.getID())), data={
                                'addtagIDs': addTagIDs})
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(resp, template.projects.profile)
        self.assertEqual(project.totalTags(), 4)

    @tag('afa')
    def test_liveData(self):
        project = Project.objects.create(name=getProjName(
        ), creator=self.profile, reponame=getProjRepo(), status=Code.APPROVED)
        resp = self.client.post(follow=True, path=root(
            url.projects.liveData(project.getID())))
        self.assertEqual(resp.status_code, HttpResponse.status_code)
        data = json.loads(resp.content.decode(Code.UTF_8))
        self.assertIsInstance(data['languages'],list)
        self.assertIsInstance(data['contributorsHTML'],str)

