from auth2.tests.utils import getTestPassword
from django.test import TestCase, tag
from main.env import BOTMAIL
from main.methods import *
from main.strings import Code, Message, classAttrsToDict, setPathParams
from people.models import Profile, User

from .utils import B64


@tag(Code.Test.METHOD, Code.Test.REST)
class MainMethodsTest(TestCase):
    @classmethod
    def setUpTestData(self) -> None:
        self.bot, _ = User.objects.get_or_create(email=BOTMAIL, defaults=dict(
            first_name='knottersbot', email=BOTMAIL, password=getTestPassword()))
        return super().setUpTestData()
    
    def setUp(self) -> None:
        Profile.KNOTBOT()
        return super().setUp()

    def test_respondJSON(self):
        response = respondJson(Code.OK)
        self.assertJSONEqual(
            str(response.content, encoding=response.charset), dict(code=Code.OK))

    def test_getDeepFilePaths(self):
        def appendWhen(path):
            return path.endswith('.html')

        self.assertEqual(len(getDeepFilePaths('template', appendWhen)), 0)
        templates = getDeepFilePaths('templates', appendWhen)
        self.assertIsInstance(templates, list)
        self.assertTrue(len(templates) > 0)

    def test_maxLengthInList(self):
        def appendWhen(path):
            return path.endswith('.html')
        templates = getDeepFilePaths('templates', appendWhen)
        self.assertIsInstance(maxLengthInList(templates), int)
        self.assertTrue(maxLengthInList(templates) > 0)

    def test_minLengthInList(self):
        def appendWhen(path):
            return path.endswith('.html')
        templates = getDeepFilePaths('templates', appendWhen)
        self.assertIsInstance(minLengthInList(templates), int)
        self.assertTrue(maxLengthInList(templates) >=
                        minLengthInList(templates))

    def test_base64ToImageFile(self):
        file = base64ToImageFile(B64)
        self.assertIsInstance(file, ContentFile)

    def test_classAttrsToDict(self):
        def conditn(key, _):
            return str(key).isupper()
        self.assertIsInstance(classAttrsToDict(Message, conditn), dict)
    
    @tag('testpathreg')
    def test_testpathRegex(self):
        self.assertFalse(testPathRegex(url.AT_NICKNAME, '/a/@knottersbot'))
        self.assertTrue(testPathRegex(url.AT_NICKNAME, '@knottersbot'))
        self.assertFalse(testPathRegex(url.people.PROFILE, url.people.profile('hello/world')))
        self.assertTrue(testPathRegex(url.people.PROFILE, url.people.profile('hello')))
        self.assertFalse(testPathRegex(url.people.PROFILE, url.people.profile('hello/')))
        self.assertTrue(testPathRegex(url.people.SETTINGTAB, url.people.settingTab('hello')))
        self.assertFalse(testPathRegex(url.people.SETTINGTAB, url.people.settingTab('hello/')))
        self.assertFalse(testPathRegex(url.management.LABEL, url.management.label('hello', 'hello/world')))
        self.assertFalse(testPathRegex(url.management.LABEL, url.management.label('hello/w', 'hello/world')))
        self.assertTrue(testPathRegex(url.management.LABEL, url.management.label('hello', 'world')))
        self.assertTrue(testPathRegex(url.management.LABEL, url.management.label('hello/', 'world')))
        self.assertTrue(testPathRegex(url.SCRIPTS_SUBAPP, url.scripts_subapp('hello', 'world')))

    @tag('deactivebypass')
    def test_allowBypassDeactivated(self):
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.ROBOTS_TXT}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.MANIFEST}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.scripts('hello')}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.scripts_subapp('hello', 'world')}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.VERSION_TXT}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.SERVICE_WORKER}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.SWITCH_LANG}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.VERIFY_CAPTCHA}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.OFFLINE}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{url.REDIRECTOR}?n=/hello/world/"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot()}{setPathParams(url.WEBPUSH_SUB, 'hello')}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot(AUTH2)}{url.Auth.LOGOUT}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot(AUTH2)}{url.Auth.ACCOUNTACTIVATION}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot(DOCS)}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot(DOCS)}{url.docs.type('world')}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot(MANAGEMENT)}{url.Management.CREATE_REPORT}"))
        self.assertTrue(allowBypassDeactivated(f"{url.getRoot(MANAGEMENT)}{url.Management.CREATE_FEED}"))
        self.assertFalse(allowBypassDeactivated(f"{url.getRoot(PROJECTS)}{url.projects.profile('hello')}"))

    @tag('numsuff')
    def test_getNumberSuffix(self):
        for i in range(1,10001):
            if str(i)[-2:] in [str(i) for i in range(11, 20)]:
                self.assertEqual(getNumberSuffix(i), 'th')
                self.assertEqual(getNumberSuffix(i, True), f'{i}th')
            elif str(i)[-1] == str(1):
                self.assertEqual(getNumberSuffix(i), 'st')
                self.assertEqual(getNumberSuffix(i, True), f'{i}st')
            elif str(i)[-1] == str(2):
                self.assertEqual(getNumberSuffix(i), 'nd')
                self.assertEqual(getNumberSuffix(i, True), f'{i}nd')
            elif str(i)[-1] == str(3):
                self.assertEqual(getNumberSuffix(i), 'rd')
                self.assertEqual(getNumberSuffix(i, True), f'{i}rd')
            else:
                self.assertEqual(getNumberSuffix(i), 'th')
                self.assertEqual(getNumberSuffix(i, True), f'{i}th')
