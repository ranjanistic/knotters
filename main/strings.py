import re
from deprecated import deprecated
from projects.apps import APPNAME as PROJECTS
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE
from moderation.apps import APPNAME as MODERATION
from management.apps import APPNAME as MANAGEMENT
from .env import CDN_URL
from auth2.apps import APPNAME as AUTH2
from django.utils.translation import gettext_lazy as _

AUTH = 'auth'
DOCS = 'docs'


def classAttrsToDict(className, appendCondition) -> dict:
    data = dict()
    for key in className.__dict__:
        if not (str(key).startswith('__') and str(key).endswith('__')):
            if appendCondition(key, className.__dict__.get(key)):
                data[key] = className.__dict__.get(key)
    return data


def setPathParams(path: str, *replacingChars: str, lookfor: str = '', extendRemaining=True) -> str:
    """
    Replaces 'lookfor' of given 'path' with given with replacingChars. Replaces each finding with each element of replacingChars.

    :path: The string (primarily url path) to be operated on.
    :replacingChars: Tuple of characters to replace findings one by one with each element. Defaults to '*' for all findings.
    :lookfor: String or pattern to be looked for and replaced in path.
    :extendRemaining: If there are more findings than provided replacingChars, the last element of replacingChars is used to replace the remaining findings.Defaults to True
    """
    lookfor = lookfor if lookfor else Code.URLPARAM
    if len(replacingChars) < 1:
        replacingChars = ['*']
    i = 0
    while i < len(replacingChars):
        path = re.sub(lookfor, str(replacingChars[i]), path, 1)
        i += 1
    return path if not extendRemaining else re.sub(lookfor, str(replacingChars[len(replacingChars)-1]), path)


def setURLAlerts(url, alert: str = '', error: str = '', success: str = '', otherQueries: bool = False) -> str:
    if error:
        error = f"{'&' if otherQueries else '?'}e={error}" if message.isValid(
            error) else ''
        otherQueries = message.isValid(error)
    if alert:
        alert = f"{'&' if otherQueries else '?' }a={alert}" if message.isValid(
            alert) else ''
        otherQueries = message.isValid(alert)
    if success:
        success = f"{'&' if otherQueries else '?'}s={success}" if message.isValid(
            success) else ''
    return f"{url}{error}{alert}{success}"


class Code():
    OK = "OK"
    PONG = "PONG"
    NO = "NO"
    JSON_BODY = "JSON_BODY"
    GET = "GET"
    POST = "POST"
    UNKNOWN_EVENT = "UNKNOWN_EVENT"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODERATION = "moderation"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    SETTING = "setting"
    INVALID_DIVISION = "INVALID_DIVISION"
    SWASSETS = 'swassets'
    MODERATOR = "moderator"
    LAST_MODERATOR = "last_moderator"
    ZOMBIE = 'Zombie'
    ZOMBIEMAIL = 'zombie@knotters.org'
    URLPARAM = r'(<str:|<int:)+[a-zA-Z0-9]+(>)'

    ACTIVE = "active"
    HISTORY = "history"
    UPCOMING = "upcoming"

    HOOK = 'hook'
    SHA256 = 'sha256'
    UTF_8 = 'utf-8'

    APPLICATION_JSON = 'application/json'
    TEXT_PLAIN = 'text/plain'
    APPLICATION_JS = 'application/javascript'

    TOPIC = 'topic'
    CATEGORY = 'category'
    TAG = 'tag'

    REPORTS = 'reports'
    FEEDBACKS = 'feedbacks'

    COMPETITIONS = 'competitions'
    MENTORSHIPS = 'mentorships'
    RESULTS = "results"
    JUDGEMENTS = 'judgements'
    MODERATIONS = 'moderations'
    FRAMEWORKS = 'frameworks'
    PEOPLE = "people"

    class Test():
        MODEL = 'model'
        VIEW = 'view'
        METHOD = 'method'
        STATIC = 'static'
        MAIL = 'mail'
        REST = 'rest'


code = Code()


class Event():
    PING = 'ping'
    PUSH = 'push'
    PR = 'pull_request'
    STAR = 'star'
    MEMBER_ADDED = 'member_added'
    MEMBER_REMOVED = 'member_removed'
    ORG = 'organization'
    TEAMS = 'team'
    CREATED = 'created'
    RELEASE = 'release'
    MARKETPLACE_PURCHASE = 'marketplace_purchase'
    PUBLISHED = 'published'

# ENVIRONMENTS = [Environment.DEVELOPMENT,
#                 Environment.TESTING, Environment.PRODUCTION]


class Message():

    ERROR_OCCURRED = _("An error occurred.")
    INVALID_REQUEST = _("Invalid request")
    INVALID_RESPONSE = _("Invalid response")
    SAVED = _("Saved")
    PROFILE_UPDATED = _(
        "Profile updated, it might take some time for changes to appear.")
    TAGS_UPDATED = _("Tags updated.")
    TOPICS_UPDATED = _("Topics updated.")
    NO_TOPICS_SELECTED = _("No topics selected")
    MAX_TAGS_ACHEIVED = _("Maximum tags limit reached.")
    NO_TAGS_SELECTED = _("No tags selected")
    MAX_TOPICS_ACHEIVED = _("Maximum topics limit reached.")
    LOGIN_REQUIRED = _("Please login to continue.")

    RESULT_DECLARED = _("Results declared!")
    RESULT_NOT_DECLARED = _("Results not declared.")
    RESULT_DECLARING = _("Results declaration in progress")
    ALREADY_PARTICIPATING = _("You're already participating.")
    PARTICIPATION_CONFIRMED = _('Participation confirmed!')
    PARTICIPATION_PROHIBITED = _(
        'You are currently not allowed to participate.')
    PARTICIPATION_WITHDRAWN = _('Participation withdrawn.')
    MEMBER_REMOVED = _('Member removed')
    INVALID_ID = _('Invalid ID')
    USER_NOT_EXIST = _('User doesn\'t exist.')
    USER_PARTICIPANT_OR_INVITED = _("User already participating or invited.")
    SUBMITTED_ALREADY = _("Already submitted")
    SUBMITTED_SUCCESS = _("Submitted successfully")
    SUBMITTED_LATE = _("Submitted, but late.")
    SUBMISSION_TOO_LATE = _("It is too late now.")
    SUBMISSION_MARKING_INVALID = _("Invalid submission markings, try again.")
    SUBMISSION_ERROR = _("Error in submission")
    NO_INTERNAL_MODERATORS = _("No moderators in available your organization")

    FREE_PROJECT_CREATED = _("Project created successfully!")
    SENT_FOR_REVIEW = _("Sent for review")
    PROJECT_DELETED = _("Project deleted")
    TERMS_UNACCEPTED = _("You have not accepted the terms")
    LICENSE_UNSELECTED = _("You have to choose a license")
    NICKNAME_ALREADY_TAKEN = _(
        "The nickname is not available, try something else.")
    CODENAME_ALREADY_TAKEN = _(
        "The codename is not available, try something else.")
    INVALID_LIC_DATA = _('Invalid license data')
    SNAP_CREATED = _("Snapshot published")
    SNAP_UPDATED = _("Snapshot updated")
    SNAP_DELETED = _("Snapshot removed")

    UNDER_MODERATION = _("Currently under moderation")
    ALREADY_RESOLVED = _("Already resolved")
    ALREADY_EXISTS = _("Already exists")
    REQ_MESSAGE_SAVED = _("Request message saved")
    RES_MESSAGE_SAVED = _("Response message saved")
    MODERATION_REAPPLIED = _("Re-applied for moderation to another moderator.")
    SETTING_APPROVED_PROJECT = _("Setting up approved project.")
    SETUP_APPROVED_PROJECT_DONE = _("Approved project setup done.")
    GH_REPO_NOT_SETUP = _("GitHub repository has not been setup yet. Check again later.")

    ACCOUNT_PREF_SAVED = _("Account preferences saved.")
    SUCCESSOR_GH_UNLINKED = _(
        'Your successor should have Github profile linked to their account.')
    SUCCESSOR_OF_PROFILE = _('You are the successor of this profile.')
    SUCCESSOR_NOT_FOUND = _('Successor not found')
    SUCCESSOR_UNSET = _('Successor not set, use default successor if none.')
    SUCCESSORSHIP_DECLINED = _(
        "You\'ve declined this profile\'s successorship")
    SUCCESSORSHIP_ACCEPTED = _(
        "You\'re now the successor of this profile\'s assets.")

    ACCOUNT_DEACTIVATED = _("Account deactivated.")
    ACCOUNT_DELETED = _("Account deleted successfully.")

    XP_ADDED = _("Profile XP increased")

    UNAUTHORIZED = _('Unauthorized access')

    INVALID_MODERATOR = _('Invalid moderator')
    COMP_TITLE_EXISTS = _('Competition with similar title exists')
    INVALID_TIME_PAIR = _('Timings are abnormal, please correct them')
    INVALID_QUALIFIER_RANK = _(
        'The qualifier rank is not valid. Use rank > 0 or 1')
    SAME_MOD_JUDGE = _('Moderator and judges should be different')
    COMP_CREATED = _("Competition created successfully")
    CERTS_GENERATED = _('Certificates generated successfully.')
    CERTS_GENERATING = _('Certificates are being generated.')
    CERT_NOT_FOUND = _('Certificate not found')

    MODERATION_SKIPPED = _(
        "That moderation was passed on to another moderator.")
    NO_MODERATORS_AVAILABLE = _("No moderators available")

    PAYMENT_REG_SUCCESS = _("You have successfully paid the registration fee")

    ALREADY_INVITED = _("Invitation already exists")
    PROJECT_TRANSFER_ACCEPTED = _("You\'re now the owner of this project.")
    PROJECT_TRANSFER_DECLINED = _(
        "You\'ve declined the ownership of this project.")
    PROJECT_MOD_TRANSFER_ACCEPTED = _("You\'re now the moderator of this project.")
    PROJECT_MOD_TRANSFER_DECLINED = _(
        "You\'ve declined the moderatorship of this project.")
    PROJECT_DEL_ACCEPTED = _("You\'ve accepted to delete the project.")
    PROJECT_DEL_DECLINED = _(
        "You\'ve declined to delete this project.")
    ALREADY_INVITED = _("User already invited.")
    JOINED_MANAGEMENT = _("You\'ve joined this organization.")
    DECLINED_JOIN_MANAGEMENT = _(
        "You\'ve declined invitation to join this organization.")

    PENDING_MODERATIONS_EXIST = _(
        "Pending unresolved moderation requests exist.")

    def isValid(self, message: str) -> bool:
        """
        Whether the given string is a valid message response to be sent to client or not. This check will ensure that
        malicious messages as url query alert/error are not being shown to someone via any url of this application.

        This requires that all response messages should be an attribute of this Message class.

        :message: The message string to be checked for validity.
        """
        def conditn(key, _):
            return str(key).isupper()
        attrs = classAttrsToDict(Message, conditn)
        validMessages = []
        for key in attrs:
            validMessages.append(attrs[key])
        return validMessages.__contains__(message)

    class Custom():

        def already_exists(something):
            return f"{something} already exists"


message = Message()


class Action():
    ACCEPT = "accept"
    DECLINE = "decline"
    CREATE = "create"
    VIEW = "view"
    UPDATE = "update"
    REMOVE = "remove"


action = Action()

DIVISIONS = [PROJECTS, PEOPLE, COMPETE, MODERATION, MANAGEMENT, AUTH2]


class Project():
    CORE_PROJECT = "core-project"
    PROJECTSTATES = [code.MODERATION, code.APPROVED, code.REJECTED]
    PROJECTSTATESCHOICES = (
        [code.MODERATION, code.MODERATION.capitalize()],
        [code.APPROVED, code.APPROVED.capitalize()],
        [code.REJECTED, code.REJECTED.capitalize()]
    )
    PALLETE = 'pallete'

project = Project()
CORE_PROJECT = Project.CORE_PROJECT

class Moderation():
    MODSTATES = [code.MODERATION, code.APPROVED, code.REJECTED]
    MODSTATESCHOICES = (
        [code.MODERATION, code.MODERATION.capitalize()],
        [code.APPROVED, code.APPROVED.capitalize()],
        [code.REJECTED, code.REJECTED.capitalize()]
    )

    TYPES = [PROJECTS, PEOPLE, COMPETE, Project.CORE_PROJECT]

    TYPECHOICES = ([PROJECTS, PROJECTS.capitalize()], [PEOPLE, PEOPLE.capitalize(
    )], [COMPETE, COMPETE.capitalize()], [Project.CORE_PROJECT,Project.CORE_PROJECT.capitalize()])


moderation = Moderation()


class Profile():
    OVERVIEW = "overview"
    PROJECTS = "projects"
    ACHEIVEMENTS = "acheivements"
    FRAMEWORKS = "frameworks"
    CONTRIBUTION = "contribution"
    ACTIVITY = "activity"
    MODERATION = "moderation"
    COMPETITIONS = "competitions"
    MENTORSHIP = "mentorship"
    PEOPLE = "people"

    class Setting():
        ACCOUNT = "account"
        PREFERENCE = "preference"
        SECURITY = "security"

    setting = Setting()


class Compete():
    ACTIVE = "active"
    UPCOMING = "upcoming"
    HISTORY = "history"
    OVERVIEW = "overview"
    TASK = "task"
    GUIDELINES = "guidelines"
    SUBMISSION = "submission"
    RESULT = "result"

    def __init__(self) -> None:
        self.COMPETE_SECTIONS = [
            self.OVERVIEW, self.TASK,
            self.GUIDELINES,
            self.SUBMISSION,
            self.RESULT
        ]


class Auth2():
    ACCOUNT = "account"
    DEVICE = "device"
    SECURITY = "security"
    PREFERENCE = "preference"

    def __init__(self) -> None:
        self.AUTH2_SECTIONS = [
            self.ACCOUNT,
            self.DEVICE,
            self.SECURITY,
            self.PREFERENCE
        ]


profile = Profile()
compete = Compete()


class Browse():
    PROJECT_SNAPSHOTS = "project-snapshots"
    NEW_PROFILES = "new-profiles"
    NEW_PROJECTS = "new-projects"
    RECENT_WINNERS = "recent-winners"
    RECOMMENDED_PROJECTS = "recommended-projects"
    TRENDING_TOPICS = "trending-topics"
    TRENDING_PROJECTS = "trending-projects"
    TRENDING_PROFILES = "trending-profiles"
    NEWLY_MODERATED = "newly-moderated"
    HIGHEST_MONTH_XP_PROFILES = "highest-month-xp-profiles"
    LATEST_COMPETITIONS = "latest-competitions"
    TRENDING_MENTORS = "trending-mentors"
    TRENDING_MODERATORS = "trending-moderators"
    DISPLAY_MENTORS = "display-mentors"

    def getAllKeys():
        def cond(key, value):
            return str(key).isupper()
        return classAttrsToDict(Browse, cond)


class URL():
    INDEX = ''
    FAVICON = 'favicon.ico'
    ROBOTS_TXT = 'robots.txt'
    MANIFEST = 'manifest.json'
    SERVICE_WORKER = 'service-worker.js'
    STRINGS = 'strings.js'
    SWITCH_LANG = 'i18n/'
    VERSION_TXT = 'version.txt'
    OFFLINE = 'off408'
    BRANDING = 'branding/'
    ROOT = '/'
    WEBPUSH = 'webpush/'
    WEBPUSH_SUB = 'webpush/<str:sub>'
    ICON_PNG = f"{CDN_URL}/graphics/self/1024/icon.png"
    AUTH = f"{AUTH}/"
    DOCS = f'{DOCS}/'
    PROJECTS = f'{PROJECTS}/'
    COMPETE = f'{COMPETE}/'
    PEOPLE = f'{PEOPLE}/'
    MODERATION = f'{MODERATION}/'
    MANAGEMENT = f'{MANAGEMENT}/'
    FAME_WALL = 'wall-of-fame/'
    REDIRECTOR = 'redirector/'

    def redirector(self, to='/'):
        return f"{self.REDIRECTOR}?n={to}"

    APPLANDING = '<str:subapp>/landing'

    def applanding(self, subapp):
        return setPathParams(self.APPLANDING, subapp)

    DOCTYPE = 'docs/<str:type>'
    LANDINGS = 'landing/'
    LANDING = 'landing/'

    BROWSER = 'browser/<str:type>'

    def browser(self, type):
        return setPathParams(self.BROWSER, type)

    VERIFY_CAPTCHA = 'captcha/verify'

    BASE_GITHUB_EVENTS = 'github-events/<str:type>/<str:targetID>/'
    VIEW_SNAPSHOT = 'snapshot/<str:snapID>/'

    ON_BOARDING = 'on-boarding/'
    ON_BOARDING_UPDATE = 'on-boarding/update'

    def view_snapshot(self, snapID):
        return setPathParams(self.VIEW_SNAPSHOT, snapID)

    def getRoot(self, fromApp: str = '', withslash=True) -> str:
        """
        Returns root path of given sub application name.

        :fromApp: The app name, if nothing or invalid value is passed, returns root.
        """
        if fromApp == AUTH2 or fromApp == AUTH:
            return f"/{self.AUTH if withslash else self.AUTH.strip('/')}"
        if fromApp == DOCS:
            return f"/{self.DOCS if withslash else self.DOCS.strip('/')}"
        if fromApp == COMPETE:
            return f"/{self.COMPETE if withslash else self.COMPETE.strip('/')}"
        elif fromApp == PROJECTS:
            return f"/{self.PROJECTS if withslash else self.PROJECTS.strip('/')}"
        elif fromApp == PEOPLE:
            return f"/{self.PEOPLE if withslash else self.PEOPLE.strip('/')}"
        elif fromApp == MODERATION:
            return f"/{self.MODERATION if withslash else self.MODERATION.strip('/')}"
        elif fromApp == MANAGEMENT:
            return f"/{self.MANAGEMENT if withslash else self.MANAGEMENT.strip('/')}"
        else:
            return self.ROOT if withslash else self.ROOT.strip('/')

    def getMessageQuery(self, alert: str = '', error: str = '', success: str = '', otherQueries: bool = False) -> str:
        if error:
            error = f"{'&' if otherQueries else '?'}e={error}" if message.isValid(
                error) else ''
            otherQueries = message.isValid(error)
        if alert:
            alert = f"{'&' if otherQueries else '?' }a={alert}" if message.isValid(
                alert) else ''
            otherQueries = message.isValid(alert)
        if success:
            success = f"{'&' if otherQueries else '?'}s={success}" if message.isValid(
                success) else ''
        return f"{error}{alert}{success}"

    def githubProfile(self, ghID):
        return f"https://github.com/{ghID}"

    class Auth():

        SIGNUP = 'signup/'
        REGISTER = 'register/'
        LOGIN = 'login/'
        SIGNIN = 'signin/'
        LOGOUT = 'logout/'
        INACTIVE = 'inactive/'
        EMAIL = 'email/'
        PASSWORD_CHANGE = 'password/change/'
        PASSWORD_SET = 'password/set/'
        CONFIRM_EMAIL = 'confirm-email/'
        PASSWORD_RESET = 'password/reset/'
        PASSWORD_RESET_DONE = 'password/reset/done/'
        PASSWORD_RESET_KEY = 'password/reset/key/'
        PASSWORD_RESET_KEY_DONE = 'password/reset/key/done/'
        SOCIAL = 'social/'
        GITHUB = 'github/'
        GOOGLE = 'google/'
        DISCORD = 'discord/'

        NOTIFY_SW = 'notify-sw.js'
        NOTIF_ENABLED = 'push-notify/enabled'
        TAB_SECTION = 'section/<str:section>/'
        VERIFY_REAUTH = 're-auth/verify/'

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Auth, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(AUTH2)}{setPathParams(urls[key])}"
            return URLS

    auth = Auth()

    class Docs():
        TYPE = '<str:type>'

        def type(self, type):
            return setPathParams(self.TYPE, type)

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Docs, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(DOCS)}{setPathParams(urls[key])}"
            return URLS

    docs = Docs()

    class Compete():
        COMPID = '<str:compID>'

        def compID(self, compID):
            return setPathParams(self.COMPID, compID)

        INDEXTAB = 'indexTab/<str:tab>'

        def indexTab(self, tab):
            return setPathParams(self.INDEXTAB, tab)

        BROWSE_SEARCH = 'browse/search'

        COMPETETABSECTION = 'competeTab/<str:compID>/<str:section>'

        def competeTabSection(self, compID, section):
            return setPathParams(self.COMPETETABSECTION, compID, section)

        DATA = "data/<str:compID>"

        def data(self, compID):
            return setPathParams(self.DATA, compID)

        PARTICIPATE = 'participate/<str:compID>'

        def participate(self, compID):
            return setPathParams(self.PARTICIPATE, compID)

        REMOVEMEMBER = 'remove/<str:subID>/<str:userID>'

        def removeMember(self, subID, userID):
            return setPathParams(self.REMOVEMEMBER, subID, userID)

        INVITE = 'invite/<str:subID>'

        def invite(self, subID):
            return setPathParams(self.INVITE, subID)

        INVITATION = 'invitation/<str:subID>/<str:userID>'

        def invitation(self, subID, userID):
            return setPathParams(self.INVITATION, subID, userID)

        INVITEACTION = 'invitation/<str:subID>/<str:userID>/<str:action>'

        def inviteAction(self, subID, userID, action):
            return setPathParams(self.INVITEACTION, subID, userID, action)

        SAVE = 'save/<str:compID>/<str:subID>'

        def save(self, compID, subID):
            return setPathParams(self.SAVE, compID, subID)

        SUBMIT = 'submit/<str:compID>/<str:subID>'

        def submit(self, compID, subID):
            return setPathParams(self.SUBMIT, compID, subID)

        SUBMITPOINTS = 'submissionpoints/<str:compID>'

        def submitPoints(self, compID):
            return setPathParams(self.SUBMITPOINTS, compID)

        DECLARERESULTS = 'declareresults/<str:compID>'

        def declareResults(self, compID):
            return setPathParams(self.DECLARERESULTS, compID)

        TOPIC_SCORES = 'scores/<str:resID>/'

        def topicscores(self, resID):
            return setPathParams(self.TOPIC_SCORES, resID)

        CLAIMXP = 'claimxp/<str:compID>/<str:subID>'

        def claimXP(self, compID, subID):
            return setPathParams(self.CLAIMXP, compID, subID)

        GENERATE_CERTS = 'generatecertificate/<str:compID>'

        def generateCert(self, compID):
            return setPathParams(self.GENERATE_CERTS, compID)

        CERT_INDEX = 'certificate/'

        def certIndex(self):
            return setPathParams(self.CERT_INDEX)

        CERT_VERIFY = 'certificate/verify'

        def certIndex(self):
            return setPathParams(self.CERT_VERIFY)

        CERTIFICATE = 'certificate/<str:resID>/<str:userID>'

        def certificate(self, resID, userID):
            return setPathParams(self.CERTIFICATE, resID, userID)

        @deprecated
        def certficate(self, resID, userID):
            return self.certificate(resID, userID)

        CERTDOWNLOAD = 'certificate/download/<str:resID>/<str:userID>'

        def certificateDownload(self, resID, userID):
            return setPathParams(self.CERTDOWNLOAD, resID, userID)

        APPR_CERTIFICATE = 'appcertificate/<str:compID>/<str:userID>'

        def apprCertificate(self, compID, userID):
            return setPathParams(self.APPR_CERTIFICATE, compID, userID)

        APPR_CERTDOWNLOAD = 'appcertificate/download/<str:compID>/<str:userID>'

        def apprCertificateDownload(self, compID, userID):
            return setPathParams(self.APPR_CERTDOWNLOAD, compID, userID)

        @deprecated
        def certficateDownload(self, resID, userID):
            return self.certificateDownload(resID, userID)

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Compete, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(COMPETE)}{setPathParams(urls[key])}"
            return URLS

    compete = Compete()

    class Moderation():
        MODID = '<str:id>'

        def modID(self, modID):
            return setPathParams(self.MODID, modID)

        MESSAGE = 'message/<str:modID>'

        def message(self, modID):
            return setPathParams(self.MESSAGE, modID)

        ACTION = 'action/<str:modID>'

        def action(self, modID):
            return setPathParams(self.ACTION, modID)

        REAPPLY = 'reapply/<str:modID>'

        def reapply(self, modID):
            return setPathParams(self.REAPPLY, modID)

        APPROVECOMPETE = 'compete/<str:modID>'

        def approveCompete(self, modID):
            return setPathParams(self.APPROVECOMPETE, modID)

        REPORT_CATEGORIES = 'report/categories/'
        REPORT_MODERATION = 'reportmoderation/'

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Moderation, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(MODERATION)}{setPathParams(urls[key])}"
            return URLS

    moderation = Moderation()

    class People():
        PROFILE = 'profile/<str:userID>'

        def profile(self, userID):
            return setPathParams(self.PROFILE, userID)

        PROFILEEDIT = 'profile/edit/<str:section>'

        def profileEdit(self, section):
            return setPathParams(self.PROFILEEDIT, section)

        PROFILETAB = 'profiletab/<str:userID>/<str:section>'

        def profileTab(self, userID, section):
            return setPathParams(self.PROFILETAB, userID, section)

        SETTINGTAB = 'settingtab/<str:section>'

        def settingTab(self, section):
            return setPathParams(self.SETTINGTAB, section)

        ACCOUNTPREFERENCES = "account/preferences"

        TOPICSEARCH = "topics/search"
        TOPICSUPDATE = "topics/update"

        ACCOUNTACTIVATION = "account/activation"
        GETSUCCESSOR = 'account/successor'
        INVITESUCCESSOR = 'account/successor/invite'
        ACCOUNTDELETE = "account/delete"

        SUCCESSORINVITE = 'invitation/successor/<str:predID>'

        def successorInvite(self, predID):
            return setPathParams(self.SUCCESSORINVITE, predID)

        SUCCESSORINVITEACTION = 'invitation/successor/action/<str:action>'

        def successorInviteAction(self, action):
            return setPathParams(self.SUCCESSORINVITEACTION, action)

        ZOMBIE = 'zombie/<str:profileID>'

        def zombie(self, profileID):
            return setPathParams(self.ZOMBIE, profileID)

        BLOCK_USER = 'blockuser/'
        UNBLOCK_USER = 'unblockuser/'
        REPORT_CATEGORIES = 'report/categories'
        REPORT_USER = 'reportuser/'

        NEWBIES = 'newbies'

        GITHUB_EVENTS = 'github-events/<str:type>/<str:event>'
        BROWSE_SEARCH = 'browse/search'

        CREATE_FRAME = 'frameworks/create'
        PUBLISH_FRAME = 'frameworks/publish'
        FRAMEWORK = 'framework/:frameworkID'

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.People, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(PEOPLE)}{setPathParams(urls[key])}"
            return URLS

    people = People()

    class Projects():

        ALLLICENSES = 'licenses/'

        LICENSE = 'licenses/<str:id>/'

        def license(self, id):
            return setPathParams(self.LICENSE, id)

        LICENSES = 'license/all/'

        ADDLICENSE = 'license/add/'

        LICENSE_SEARCH = 'license/search/'

        CREATEVALIDATEFIELD = 'create/validate/<str:field>'

        def createValidField(self, field):
            return setPathParams(self.CREATEVALIDATEFIELD, field)

        CREATE = 'create/'

        def create(self):
            return self.CREATE

        CREATE_FREE = 'create/0/'

        def createFree(self):
            return self.CREATE_FREE

        CREATE_MOD = 'create/1/'

        def createMod(self, step: int = 0):
            return f"{self.CREATE_MOD}?step={step}"

        CREATE_CORE = 'create/2/'

        def createCore(self):
            return self.CREATE_CORE

        SUBMIT_FREE = 'submit/0/'
        SUBMIT_MOD = 'submit/1/'
        SUBMIT_CORE = 'submit/2/'

        """ deprecated """
        SUBMIT = SUBMIT_MOD

        TRASH = 'trash/<str:projID>/'

        def trash(self, projID):
            return setPathParams(self.TRASH, projID)

        PROFILE_FREE = 'profile/<str:nickname>'

        def profileFree(self, nickname):
            return setPathParams(self.PROFILE_FREE, nickname)


        PROFILE_MOD = 'profile/<str:reponame>'

        def profileMod(self, reponame):
            return setPathParams(self.PROFILE_MOD, reponame)

        PROFILE_CORE = 'profile/<str:codename>'

        def profileCore(self, codename):
            return setPathParams(self.PROFILE_CORE, codename)

        PROFILE = PROFILE_MOD

        @deprecated
        def profile(self, reponame):
            return self.profileMod(reponame)

        PROFILEEDIT = 'profile/edit/<str:projectID>/<str:section>/'

        def profileEdit(self, projectID, section):
            return setPathParams(self.PROFILEEDIT, projectID, section)

        MANAGE_ASSETS = 'assets/<str:projectID>/<str:action>'

        def manageAssets(self, projectID, action):
            return setPathParams(self.MANAGE_ASSETS, projectID, action)

        TOPICSEARCH = "topics/search/<str:projID>/"

        def topicsSearch(self, projID):
            return setPathParams(self.TOPICSEARCH, projID)
        TOPICSUPDATE = "topics/update/<str:projID>/"

        def topicsUpdate(self, projID):
            return setPathParams(self.TOPICSUPDATE, projID)

        TAGSEARCH = "tags/search/<str:projID>/"

        def tagsSearch(self, projID):
            return setPathParams(self.TAGSEARCH, projID)
        TAGSUPDATE = "tags/update/<str:projID>/"

        def tagsUpdate(self, projID):
            return setPathParams(self.TAGSUPDATE, projID)

        USER_GH_REPOS = "github/user/repos"
        LINK_FREE_REPO = "github/user/repos/link"
        UNLINK_FREE_REPO = "github/user/repos/unlink"

        LIVEDATA = 'livedata/<str:projID>/'

        def liveData(self, projectID):
            return setPathParams(self.LIVEDATA, projectID)

        GITHUB_EVENTS = 'github-events/<str:type>/<str:projID>'

        def githubEvents(self, type, event, projID):
            return setPathParams(self.GITHUB_EVENTS, type, event, projID)

        GITHUB_EVENTS_FREE = 'github-events-0/<str:type>/<str:projID>'

        NEWBIES = 'newbies/'
        BROWSE_SEARCH = 'browse/search/'
        SNAPSHOTS = 'snapshots/<str:projID>/<int:limit>/'
        SNAPSHOT = 'snapshot/<str:projID>/<str:action>/'

        REPORT_CATEGORIES = 'report/categories'
        REPORT_PROJECT = 'reportproject/'
        REPORT_SNAPSHOT = 'reportsnapshot/'

        TOGGLE_ADMIRATION = 'admiration/<str:projID>/'
        TOGGLE_SNAP_ADMIRATION = 'admiration/snapshot/<str:snapID>/'
        INVITE_PROJECT_OWNER = 'invite/ownership/'
        INVITE_VERPROJECT_MOD = 'invite/ownership/1'
        INVITE_COREPROJECT_MOD = 'invite/ownership/2'

        PROJECT_TRANS_INVITE = 'invitation/transfer/<str:inviteID>'

        def projectTransInvite(self, inviteID):
            return setPathParams(self.PROJECT_TRANS_INVITE, inviteID)

        PROJECT_TRANS_INVITE_ACT = 'invitation/action/transfer/<str:inviteID>'

        def projectTransInviteAct(self, inviteID):
            return setPathParams(self.PROJECT_TRANS_INVITE_ACT, inviteID)

        VER_MOD_TRANS_INVITE = 'invitation/modtransfer/1/<str:inviteID>'

        def verifiedModTransInvite(self, inviteID):
            return setPathParams(self.VER_MOD_TRANS_INVITE, inviteID)

        CORE_MOD_TRANS_INVITE = 'invitation/modtransfer/2/<str:inviteID>'

        def coreModTransInvite(self, inviteID):
            return setPathParams(self.CORE_MOD_TRANS_INVITE, inviteID)


        VER_MOD_TRANS_INVITE_ACT = 'invitation/action/modtransfer/1/<str:inviteID>'

        def verifiedModTransInviteAct(self, inviteID):
            return setPathParams(self.VER_MOD_TRANS_INVITE_ACT, inviteID)

        CORE_MOD_TRANS_INVITE_ACT = 'invitation/action/modtransfer/2/<str:inviteID>'

        def coreModTransInviteAct(self, inviteID):
            return setPathParams(self.CORE_MOD_TRANS_INVITE_ACT, inviteID)

        VER_DEL_REQUEST = 'invitation/delrequest/1/<str:inviteID>'

        def verDeletionRequest(self, inviteID):
            return setPathParams(self.VER_DEL_REQUEST, inviteID)

        CORE_DEL_REQUEST = 'invitation/delrequest/2/<str:inviteID>'

        def coreDeletionRequest(self, inviteID):
            return setPathParams(self.CORE_DEL_REQUEST, inviteID)

        VER_DEL_REQUEST_ACT = 'invitation/action/delrequest/1/<str:inviteID>'

        def verDeletionRequestAct(self, inviteID):
            return setPathParams(self.VER_DEL_REQUEST_ACT, inviteID)

        CORE_DEL_REQUEST_ACT = 'invitation/action/delrequest/2/<str:inviteID>'

        def coreDeletionRequestAct(self, inviteID):
            return setPathParams(self.CORE_DEL_REQUEST_ACT, inviteID)

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Projects, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(PROJECTS)}{setPathParams(urls[key])}"
            return URLS

    projects = Projects()

    class Management():

        COMPETITIONS = 'competitions'
        CREATE_COMP = 'competitions/create'
        SUBMIT_COMP = 'competitions/submit'
        COMPETITION = 'competitions/<str:compID>'

        def competition(self, compID):
            return setPathParams(self.COMPETITION, compID)
        TOPICSEARCH = 'topicsearch'
        JUDGESEARCH = 'judgesearch'

        MODSEARCH = 'moderatorsearch'
        ELGIBLE_MODSEARCH = 'moderatorsearch/eligible'
        ELGIBLE_MNTSEARCH = 'mentorsearch/eligible'

        CREATE_REPORT = 'report-feedback/reports/create'
        CREATE_FEED = 'report-feedback/feedbacks/create'
        REPORT_FEED = 'report-feedback'
        REPORT_FEED_TYPE = 'report-feedback/<str:type>'

        def reportfeedType(self, type):
            return setPathParams(self.REPORT_FEED_TYPE, type)

        REPORT_FEED_TYPEID = 'report-feedback/<str:type>/<str:ID>'

        def reportfeedTypeID(self, type, ID):
            return setPathParams(self.REPORT_FEED_TYPEID, type, ID)

        COMMUNITY = 'community'
        MODERATORS = 'community/moderators'
        REMOVE_MODERATOR = 'community/moderators/remove'
        ADD_MODERATOR = 'community/moderators/add'
        MENTORS = 'community/mentors'
        REMOVE_MENTOR = 'community/mentors/remove'
        ADD_MENTOR = 'community/mentors/add'
        LABELS = 'community/labels'
        LABEL_TYPE = 'community/labels/<str:type>'

        def labelType(self, type) -> str:
            return setPathParams(self.LABEL_TYPE, type)

        LABEL = 'community/labels/<str:type>/<str:labelID>'

        def label(self, type, labelID):
            return setPathParams(self.LABEL, type, labelID)

        LABEL_CREATE = 'community/labels/<str:type>/create'

        def labelCreate(self, type):
            return setPathParams(self.LABEL_CREATE, type)

        LABEL_UPDATE = 'community/labels/<str:type>/<str:labelID>/update'

        def labelUpdate(self, type, labelID):
            return setPathParams(self.LABEL_UPDATE, type, labelID)

        LABEL_DELETE = 'community/labels/<str:type>/<str:labelID>/delete'

        def labelDelete(self, type, labelID):
            return setPathParams(self.LABEL_DELETE, type, labelID)

        LABEL_TOPICS = 'community/labels/topics'
        LABEL_CATEGORYS = 'community/labels/categories'

        PEOPLE_MGM_SEND_INVITE = 'invite/people'

        PEOPLE_MGM_INVITE = 'invitation/people/<str:inviteID>'

        def peopleMGMInvite(self, inviteID):
            return setPathParams(self.PEOPLE_MGM_INVITE, inviteID)

        PEOPLE_MGM_INVITE_ACT = 'invitation/action/people/<str:inviteID>'

        def peopleMGMInviteAct(self, inviteID):
            return setPathParams(self.PEOPLE_MGM_INVITE_ACT, inviteID)

        PEOPLE_MGM_REMOVE = 'people/remove'

        def peopleMGMRemove(self):
            return setPathParams(self.PEOPLE_MGM_REMOVE)

        def getURLSForClient(self) -> dict:
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Management, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(MANAGEMENT)}{setPathParams(urls[key])}"
            return URLS

    managemnt = Management()
    management = Management()

    def getURLSForClient(self) -> dict:
        URLS = dict()

        def cond(key, value):
            return str(key).isupper()
        urls = classAttrsToDict(URL, cond)

        for key in urls:
            URLS[key] = f"{url.getRoot() if urls[key] != url.getRoot() else ''}{setPathParams(urls[key])}"
        return URLS


url = URL()


class Template():

    ROBOTS_TXT = "robots.txt"
    SW_JS = "service-worker.js"
    STRINGS = "strings.js"
    VERSION = "version.txt"
    MANIFEST_JSON = "manifest.json"

    INDEX = 'index'

    @property
    def index(self):
        return f'{self.INDEX}.html'

    OFFLINE = 'offline'

    @property
    def offline(self):
        return f'{self.OFFLINE}.html'

    BRANDING = 'branding'

    @property
    def branding(self):
        return f'{self.BRANDING}.html'

    FORWARD = 'forward'

    @property
    def forward(self):
        return f'{self.FORWARD}.html'

    ON_BOARDING = 'on-boarding'

    @property
    def on_boarding(self):
        return f'{self.ON_BOARDING}.html'

    LANDING = 'landing'

    @property
    def landing(self):
        return f'{self.LANDING}.html'

    FAME_WALL = 'famewall'

    @property
    def famewall(self):
        return f'{self.FAME_WALL}.html'

    INVITATION = 'invitation'

    @property
    def invitation(self):
        return f'{self.INVITATION}.html'

    SNAPSHOTS = 'snapshots'

    @property
    def snapshots(self):
        return f'{self.SNAPSHOTS}.html'

    VIEW_SNAPSHOT = 'view_snapshot'

    @property
    def view_snapshot(self):
        return f'{self.VIEW_SNAPSHOT}.html'

    class Auth():
        DIRNAME = 'account'
        DIRNAME2 = 'auth2'
        INDEX = 'index'

        ACCOUNT_INACTIVE = 'account_inactive'

        @property
        def account_inactive(self):
            return f"{self.DIRNAME}/{self.ACCOUNT_INACTIVE}.html"

        EMAIL = 'email'

        @property
        def email(self):
            return f"{self.DIRNAME}/{self.EMAIL}.html"

        EMAIL_CONFIRM = 'email_confirm'

        @property
        def email_confirm(self):
            return f"{self.DIRNAME}/{self.EMAIL_CONFIRM}.html"

        LOGIN = 'login'

        @property
        def login(self):
            return f"{self.DIRNAME}/{self.LOGIN}.html"

        LOGOUT = 'logout'

        @property
        def logout(self):
            return f"{self.DIRNAME}/{self.LOGOUT}.html"

        PASSWORD_CHANGE = 'password_change'

        @property
        def password_change(self):
            return f"{self.DIRNAME}/{self.PASSWORD_CHANGE}.html"

        PASSWORD_RESET = 'password_reset'

        @property
        def password_reset(self):
            return f"{self.DIRNAME}/{self.PASSWORD_RESET}.html"

        PASSWORD_RESET_DONE = 'password_reset_done'

        @property
        def password_reset_done(self):
            return f"{self.DIRNAME}/{self.PASSWORD_RESET_DONE}.html"

        PASSWORD_RESET_FROM_KEY = 'password_reset_from_key'

        @property
        def password_reset_from_key(self):
            return f"{self.DIRNAME}/{self.PASSWORD_RESET_FROM_KEY}.html"

        PASSWORD_RESET_FROM_KEY_DONE = 'password_reset_from_key_done'

        @property
        def password_reset_from_key_done(self):
            return f"{self.DIRNAME}/{self.PASSWORD_RESET_FROM_KEY_DONE}.html"

        PASSWORD_SET = 'password_set'

        @property
        def password_set(self):
            return f"{self.DIRNAME}/{self.PASSWORD_SET}.html"

        SIGNUP = 'signup'

        @property
        def signup(self):
            return f"{self.DIRNAME}/{self.SIGNUP}.html"

        SIGNUP_CLOSED = 'signup_closed'

        @property
        def signup_closed(self):
            return f"{self.DIRNAME}/{self.SIGNUP_CLOSED}.html"

        VERIFICATION_SENT = 'verification_sent'

        @property
        def verification_sent(self):
            return f"{self.DIRNAME}/{self.VERIFICATION_SENT}.html"

        VERIFIED_EMAIL_REQUIRED = 'verified_email_required'

        @property
        def verified_email_required(self):
            return f"{self.DIRNAME}/{self.VERIFIED_EMAIL_REQUIRED}.html"

        NOTIFY_SW_JS = "notify-sw.js"
        @property
        def notify_sw_js(self):
            return f"{self.DIRNAME2}/{self.NOTIFY_SW_JS}"

    auth = Auth()

    class Docs():
        DIRNAME = DOCS
        INDEX = 'index'

        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        DOC = 'doc'

        @property
        def doc(self):
            return f'{self.DIRNAME}/{self.DOC}.html'

    docs = Docs()

    class Compete():
        DIRNAME = COMPETE
        INDEX = "index"

        BROWSE_SEARCH = 'browse/search'

        @property
        def browse_search(self):
            return f'{self.DIRNAME}/{self.BROWSE_SEARCH}.html'

        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        ACTIVE = f"index/{Compete.ACTIVE}"

        @property
        def active(self):
            return f'{self.DIRNAME}/{self.ACTIVE}.html'

        UPCOMING = f"index/{Compete.UPCOMING}"

        @property
        def upcoming(self):
            return f'{self.DIRNAME}/{self.UPCOMING}.html'

        HISTORY = f"index/{Compete.HISTORY}"

        @property
        def history(self):
            return f'{self.DIRNAME}/{self.HISTORY}.html'

        LANDING = 'landing'

        @property
        def landing(self):
            return f'{self.DIRNAME}/{self.LANDING}.html'

        PROFILE = 'profile'

        @property
        def profile(self):
            return f'{self.DIRNAME}/{self.PROFILE}.html'

        CERT_INDEX = 'certificate/index'

        @property
        def cert_index(self):
            return f'{self.DIRNAME}/{self.CERT_INDEX}.html'

        CERT_CERTIFICATE = 'certificate/certificate'

        @property
        def cert_certificate(self):
            return f'{self.DIRNAME}/{self.CERT_CERTIFICATE}.html'

        CERT_APPCERTIFICATE = 'certificate/certificate-app'

        @property
        def cert_appcertificate(self):
            return f'{self.DIRNAME}/{self.CERT_APPCERTIFICATE}.html'

        INVITATION = 'invitation'

        @property
        @deprecated
        def invitation(self):
            return f'{self.DIRNAME}/{self.INVITATION}.html'

        CERTIFICATE = 'certificate'

        @property
        @deprecated
        def certificate(self):
            return f'{self.DIRNAME}/{self.CERT_CERTIFICATE}.html'

        PROFILE_OVERVIEW = f"profile/{Compete.OVERVIEW}"

        @property
        def profile_overview(self):
            return f'{self.DIRNAME}/{self.PROFILE_OVERVIEW}.html'

        PROFILE_TASK = f"profile/{Compete.TASK}"

        @property
        def profile_task(self):
            return f'{self.DIRNAME}/{self.PROFILE_TASK}.html'

        PROFILE_GUIDELINES = f"profile/{Compete.GUIDELINES}"

        @property
        def profile_guidelines(self):
            return f'{self.DIRNAME}/{self.PROFILE_GUIDELINES}.html'

        PROFILE_SUBMISSION = f"profile/{Compete.SUBMISSION}"

        @property
        def profile_submission(self):
            return f'{self.DIRNAME}/{self.PROFILE_SUBMISSION}.html'

        PROFILE_RESULT = f"profile/{Compete.RESULT}"

        @property
        def profile_result(self):
            return f'{self.DIRNAME}/{self.PROFILE_RESULT}.html'

        BROWSE_RECENT_WINNERS = "browse/recent-winners"

        @property
        def browse_recent_winners(self):
            return f'{self.DIRNAME}/{self.BROWSE_RECENT_WINNERS}.html'

        BROWSE_LATEST_COMP = "browse/latest-competitions"

        @property
        def browse_latest_comp(self):
            return f'{self.DIRNAME}/{self.BROWSE_LATEST_COMP}.html'

    compete = Compete()

    class People():
        DIRNAME = PEOPLE
        LANDING = 'landing'

        @property
        def landing(self):
            return f'{self.DIRNAME}/{self.LANDING}.html'

        INDEX = 'index'

        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        PROFILE = 'profile'

        @property
        def profile(self):
            return f'{self.DIRNAME}/{self.PROFILE}.html'

        INVITATION = 'invitation'

        @property
        def invitation(self):
            return f'{self.DIRNAME}/{self.INVITATION}.html'

        BROWSE_NEWBIE = 'browse/newbie'

        @property
        def browse_newbie(self):
            return f'{self.DIRNAME}/{self.BROWSE_NEWBIE}.html'

        BROWSE_SEARCH = 'browse/search'

        @property
        def browse_search(self):
            return f'{self.DIRNAME}/{self.BROWSE_SEARCH}.html'

        BROWSE_TRENDING_MENTORS = 'browse/trending-mentors'

        @property
        def trending_mentors(self):
            return f'{self.DIRNAME}/{self.BROWSE_TRENDING_MENTORS}.html'

        BROWSE_TRENDING_MODS = 'browse/trending-moderators'

        @property
        def trending_mods(self):
            return f'{self.DIRNAME}/{self.BROWSE_TRENDING_MODS}.html'

        BROWSE_DISPLAY_MENTORS = 'browse/display-mentors'

        @property
        def display_mentors(self):
            return f'{self.DIRNAME}/{self.BROWSE_DISPLAY_MENTORS}.html'

        PROFILE_OVERVIEW = f"profile/{Profile.OVERVIEW}"

        @property
        def profile_overview(self):
            return f'{self.DIRNAME}/{self.PROFILE_OVERVIEW}.html'

        PROFILE_PROJECTS = f"profile/{Profile.PROJECTS}"

        @property
        def profile_projects(self):
            return f'{self.DIRNAME}/{self.PROFILE_PROJECTS}.html'

        PROFILE_ACHEIVEMENTS = f"profile/{Profile.ACHEIVEMENTS}"

        @property
        def profile_acheivements(self):
            return f'{self.DIRNAME}/{self.PROFILE_ACHEIVEMENTS}.html'

        PROFILE_CONTRIBUTION = f"profile/{Profile.CONTRIBUTION}"

        @property
        def profile_contribution(self):
            return f'{self.DIRNAME}/{self.PROFILE_CONTRIBUTION}.html'

        PROFILE_ACTIVITY = f"profile/{Profile.ACTIVITY}"

        @property
        def profile_activity(self):
            return f'{self.DIRNAME}/{self.PROFILE_ACTIVITY}.html'

        PROFILE_MODERATION = f"profile/{Profile.MODERATION}"

        @property
        def profile_moderation(self):
            return f'{self.DIRNAME}/{self.PROFILE_MODERATION}.html'

        PROFILE_FRAMEWORK = f"profile/{Profile.FRAMEWORKS}"

        @property
        def profile_framework(self):
            return f'{self.DIRNAME}/{self.PROFILE_FRAMEWORK}.html'

        SETTING_ACCOUNT = f"setting/{Profile.Setting.ACCOUNT}"

        @property
        def setting_account(self):
            return f'{self.DIRNAME}/{self.SETTING_ACCOUNT}.html'
        SETTING_PREFERENCE = f"setting/{Profile.Setting.PREFERENCE}"

        @property
        def setting_preference(self):
            return f'{self.DIRNAME}/{self.SETTING_PREFERENCE}.html'
        SETTING_SECURITY = f"setting/{Profile.Setting.SECURITY}"

        @property
        def setting_security(self):
            return f'{self.DIRNAME}/{self.SETTING_SECURITY}.html'

        FRAMEWORK_CREATE = f"framework/create"

        @property
        def framework_create(self):
            return f'{self.DIRNAME}/{self.FRAMEWORK_CREATE}.html'

    people = People()

    class Projects():
        DIRNAME = PROJECTS
        LANDING = 'landing'

        @property
        def landing(self):
            return f'{self.DIRNAME}/{self.LANDING}.html'
        INDEX = 'index'

        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        PROFILE_FREE = 'profile/0'

        @property
        def profile_free(self):
            return f'{self.DIRNAME}/{self.PROFILE_FREE}.html'

        PROFILE_MOD = 'profile/1'

        @property
        def profile_mod(self):
            return f'{self.DIRNAME}/{self.PROFILE_MOD}.html'

        PROFILE_CORE = 'profile/2'

        @property
        def profile_core(self):
            return f'{self.DIRNAME}/{self.PROFILE_CORE}.html'

        PROFILE = PROFILE_MOD

        @property
        def profile(self):
            return self.profile_mod

        CREATE = 'create'

        @property
        def create(self):
            return f'{self.DIRNAME}/{self.CREATE}.html'

        CREATE_FREE = 'create/0'

        @property
        def create_free(self):
            return f'{self.DIRNAME}/{self.CREATE_FREE}.html'

        CREATE_MOD = 'create/1'

        @property
        def create_mod(self):
            return f'{self.DIRNAME}/{self.CREATE_MOD}.html'

        CREATE_CORE = 'create/2'

        @property
        def create_core(self):
            return f'{self.DIRNAME}/{self.CREATE_CORE}.html'

        INVITATION = 'invitation'

        @property
        def invitation(self):
            return f'{self.DIRNAME}/{self.INVITATION}.html'

        CORE_M_INVITATION = 'coremodinvite'

        @property
        def coremodinvite(self):
            return f'{self.DIRNAME}/{self.CORE_M_INVITATION}.html'

        VER_M_INVITATION = 'vermodinvite'

        @property
        def vermodinvite(self):
            return f'{self.DIRNAME}/{self.VER_M_INVITATION}.html'

        VER_DEL_INVITATION = 'verdelinvite'

        @property
        def verdelinvite(self):
            return f'{self.DIRNAME}/{self.VER_DEL_INVITATION}.html'

        CORE_DEL_INVITATION = 'coredelinvite'

        @property
        def coredelinvite(self):
            return f'{self.DIRNAME}/{self.CORE_DEL_INVITATION}.html'

        LICENSE_INDEX = 'license/index'

        @property
        def license_index(self):
            return f'{self.DIRNAME}/{self.LICENSE_INDEX}.html'

        LICENSE_LIC = 'license/license'

        @property
        def license_lic(self):
            return f'{self.DIRNAME}/{self.LICENSE_LIC}.html'

        PROFILE_CONTRIBS = 'profile/contributors'

        @property
        def profile_contribs(self):
            return f'{self.DIRNAME}/{self.PROFILE_CONTRIBS}.html'

        BROWSE_NEWBIE = 'browse/newbie'

        @property
        def browse_newbie(self):
            return f'{self.DIRNAME}/{self.BROWSE_NEWBIE}.html'

        BROWSE_RECOMMENDED = 'browse/recommended'

        @property
        def browse_recommended(self):
            return f'{self.DIRNAME}/{self.BROWSE_RECOMMENDED}.html'

        BROWSE_TRENDING = 'browse/trending'

        @property
        def browse_trending(self):
            return f'{self.DIRNAME}/{self.BROWSE_TRENDING}.html'

        BROWSE_SEARCH = 'browse/search'

        @property
        def browse_search(self):
            return f'{self.DIRNAME}/{self.BROWSE_SEARCH}.html'

        LICENSE_SEARCH = 'license/search'

        @property
        def license_search(self):
            return f'{self.DIRNAME}/{self.LICENSE_SEARCH}.html'

        SNAPSHOTS = 'snapshots'

        @property
        def snapshots(self):
            return f'{self.DIRNAME}/{self.SNAPSHOTS}.html'

    projects = Projects()

    class Moderation():
        DIRNAME = MODERATION

        INDEX = 'index'

        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        PROJECTS = 'projects'

        @property
        def projects(self):
            return f'{self.DIRNAME}/{self.PROJECTS}.html'

        PEOPLE = 'people'

        @property
        def people(self):
            return f'{self.DIRNAME}/{self.PEOPLE}.html'

        COMPETE = 'compete'

        @property
        def compete(self):
            return f'{self.DIRNAME}/{self.COMPETE}.html'

        CORE_PROJECT = 'core-project'

        @property
        def coreproject(self):
            return f'{self.DIRNAME}/{self.CORE_PROJECT}.html'

    moderation = Moderation()

    class Management():
        DIRNAME = MANAGEMENT

        INDEX = 'index'

        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        COMP_INDEX = 'competition/index'

        @property
        def comp_index(self):
            return f'{self.DIRNAME}/{self.COMP_INDEX}.html'

        COMP_CREATE = 'competition/create'

        @property
        def comp_create(self):
            return f'{self.DIRNAME}/{self.COMP_CREATE}.html'

        COMP_COMPETE = 'competition/compete'

        @property
        def comp_compete(self):
            return f'{self.DIRNAME}/{self.COMP_COMPETE}.html'

        REPORTFEED_INDEX = 'reportFeed/index'

        @property
        def reportfeed_index(self):
            return f'{self.DIRNAME}/{self.REPORTFEED_INDEX}.html'

        REPORTFEED_FEEDBACKS = 'reportFeed/feedbacks'

        @property
        def reportfeed_feedbacks(self):
            return f'{self.DIRNAME}/{self.REPORTFEED_FEEDBACKS}.html'

        REPORTFEED_FEEDBACK = 'reportFeed/feedback'

        @property
        def reportfeed_feedback(self):
            return f'{self.DIRNAME}/{self.REPORTFEED_FEEDBACK}.html'

        REPORTFEED_REPORTS = 'reportFeed/reports'

        @property
        def reportfeed_reports(self):
            return f'{self.DIRNAME}/{self.REPORTFEED_REPORTS}.html'

        REPORTFEED_REPORT = 'reportFeed/report'

        @property
        def reportfeed_reports(self):
            return f'{self.DIRNAME}/{self.REPORTFEED_REPORT}.html'

        COMMUNITY_INDEX = 'community/index'

        @property
        def community_index(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_INDEX}.html'

        COMMUNITY_LABELS = 'community/labels'

        @property
        def community_labels(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_LABELS}.html'

        COMMUNITY_LABELS_CATEGORIES = 'community/labels/categories'

        @property
        def community_labels_categories(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_LABELS_CATEGORIES}.html'

        COMMUNITY_LABELS_TAGS = 'community/labels/tags'

        @property
        def community_labels_tags(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_LABELS_TAGS}.html'

        COMMUNITY_CATEGORY = 'community/category'

        @property
        def community_category(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_CATEGORY}.html'

        COMMUNITY_LABELS_TOPICS = 'community/labels/topics'

        @property
        def community_labels(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_LABELS}.html'

        COMMUNITY_TOPIC = 'community/topic'

        @property
        def community_topic(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_TOPIC}.html'

        COMMUNITY_MODERATORS = 'community/moderators'

        @property
        def community_moderators(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_MODERATORS}.html'

        COMMUNITY_MENTORS = 'community/mentors'

        @property
        def community_mentors(self):
            return f'{self.DIRNAME}/{self.COMMUNITY_MENTORS}.html'

        INVITATION = 'invitation'

        @property
        def invitation(self):
            return f'{self.DIRNAME}/{self.INVITATION}.html'

    management = Management()


template = Template()
