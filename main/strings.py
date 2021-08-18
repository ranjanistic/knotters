import re
from projects.apps import APPNAME as PROJECTS
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE
from moderation.apps import APPNAME as MODERATION
from management.apps import APPNAME as MANAGEMENT

AUTH = 'auth'
DOCS = 'docs'

class Code():
    OK = "OK"
    NO = "NO"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODERATION = "moderation"
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    SETTING = "setting"
    INVALID_DIVISION = "INVALID_DIVISION"
    SWASSETS = 'swassets'
    MODERATOR = "moderator"
    ZOMBIE = 'Zombie'
    ZOMBIEMAIL = 'zombie@knotters.org'
    URLPARAM = r'(<str:|<int:)+[a-zA-Z0-9]+(>)'

    HOOK = 'hook'

    TOPIC = 'topic'
    CATEGORY = 'category'

    RESULTS = "results"

    class Test():
        MODEL = 'model'
        VIEW = 'view'
        METHOD = 'method'
        STATIC = 'static'


code = Code()

class Event():
    PING = 'ping'
    PUSH = 'push'
    PR = 'pull_request'

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


# ENVIRONMENTS = [Environment.DEVELOPMENT,
#                 Environment.TESTING, Environment.PRODUCTION]


class Message():
    ERROR_OCCURRED = "An error occurred."
    INVALID_REQUEST = "Invalid request"
    INVALID_RESPONSE = "Invalid response"
    SAVED = "Saved"

    RESULT_DECLARED = "Results declared!"
    ALREADY_PARTICIPATING = "You're already participating."
    PARTICIPATION_WITHDRAWN = 'Participation withdrawn.'
    MEMBER_REMOVED = 'Member removed'
    INVALID_ID = 'Invalid ID'
    USER_NOT_EXIST = 'User doesn\'t exist.'
    USER_PARTICIPANT_OR_INVITED = "User already participating or invited."
    SUBMITTED_ALREADY = "Already submitted"
    SUBMITTED_SUCCESS = "Submitted successfully"
    SUBMITTED_LATE = "Submitted, but late."
    SUBMISSION_TOO_LATE = "It is too late now."
    SUBMISSION_MARKING_INVALID = "Invalid submission markings, try again."
    SUBMISSION_ERROR = "Error in submission"

    SENT_FOR_REVIEW = "Sent for review"
    PROJECT_DELETED = "Project deleted"
    TERMS_UNACCEPTED = "You have not accepted the terms"
    LICENSE_UNSELECTED = "You have to choose a license"

    UNDER_MODERATION = "Currently under moderation"
    ALREADY_RESOLVED = "Already resolved"
    REQ_MESSAGE_SAVED = "Request message saved"
    RES_MESSAGE_SAVED = "Response message saved"
    MODERATION_REAPPLIED = "Re-applied for moderation to another moderator."

    ACCOUNT_PREF_SAVED = "Account preferences saved."
    SUCCESSOR_GH_UNLINKED = 'Your successor should have Github profile linked to their account.'
    SUCCESSOR_OF_PROFILE = 'You are the successor of this profile.'
    SUCCESSOR_NOT_FOUND = 'Successor not found'
    SUCCESSOR_UNSET = 'Successor not set, use default successor if none.'
    SUCCESSORSHIP_DECLINED = "You\'ve declined this profile\'s successorship"
    SUCCESSORSHIP_ACCEPTED = "You\'re now the successor of this profile\'s assets."

    ACCOUNT_DEACTIVATED = "Account deactivated."
    ACCOUNT_DELETED = "Account deleted successfully."

    XP_ADDED = "Profile XP increased"

    UNAUTHORIZED = 'Unauthorized access'

    INVALID_MODERATOR = 'Invalid moderator'
    COMP_TITLE_EXISTS = 'Competition with similar title exists'

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


message = Message()


class Action():
    ACCEPT = "accept"
    DECLINE = "decline"


action = Action()

DIVISIONS = [PROJECTS, PEOPLE, COMPETE, MODERATION, MANAGEMENT]

class Project():
    PROJECTSTATES = [code.MODERATION, code.APPROVED, code.REJECTED]
    PROJECTSTATESCHOICES = (
        [code.MODERATION, code.MODERATION.capitalize()],
        [code.APPROVED, code.APPROVED.capitalize()],
        [code.REJECTED, code.REJECTED.capitalize()]
    )
    PALLETE = 'pallete'


project = Project()


class Moderation():
    MODSTATES = [code.MODERATION, code.APPROVED, code.REJECTED]
    MODSTATESCHOICES = (
        [code.MODERATION, code.MODERATION.capitalize()],
        [code.APPROVED, code.APPROVED.capitalize()],
        [code.REJECTED, code.REJECTED.capitalize()]
    )

    TYPES = [PROJECTS, PEOPLE, COMPETE]

    TYPECHOICES = ([PROJECTS, PROJECTS.capitalize()], [PEOPLE, PEOPLE.capitalize(
    )], [COMPETE, COMPETE.capitalize()])


moderation = Moderation()


class Profile():
    OVERVIEW = "overview"
    PROJECTS = "projects"
    ACHEIVEMENTS = "acheivements"
    CONTRIBUTION = "contribution"
    ACTIVITY = "activity"
    MODERATION = "moderation"
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


profile = Profile()
compete = Compete()

class URL():
    INDEX = ''
    FAVICON = 'favicon.ico'
    ROBOTS_TXT = 'robots.txt'
    MANIFEST = 'manifest.json'
    SERVICE_WORKER = 'service-worker.js'
    OFFLINE = 'off408'
    ROOT = '/'
    AUTH = f"{AUTH}/"
    DOCS = f'{DOCS}/'
    PROJECTS = f'{PROJECTS}/'
    COMPETE = f'{COMPETE}/'
    PEOPLE = f'{PEOPLE}/'
    MODERATION = f'{MODERATION}/'
    MANAGEMENT = f'{MANAGEMENT}/'
    REDIRECTOR = 'redirector/'
    def redirector(self,to='/'):
        return f"{self.REDIRECTOR}?n={to}"

    DOCTYPE = 'docs/<str:type>'
    LANDINGS = 'landing/'
    LANDING = 'landing'
    APPLANDING = '<str:subapp>/landing'

    def applanding(self, subapp):
        return setPathParams(self.APPLANDING,subapp)

    def getRoot(self, fromApp: str = '', withslash=True) -> str:
        """
        Returns root path of given sub application name.

        :fromApp: The app name, if nothing or invalid value is passed, returns root.
        """
        if fromApp == AUTH:
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
        elif fromApp == 'docs':
            return f"/{self.DOCS if withslash else self.DOCS.strip('/')}"
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
        LOGIN = 'login/'
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
        GOOGLE = 'gitHub/'
        GITHUB = 'google/'
        DISCORD = 'discord/'

    auth = Auth()
                
    class Docs():
        TYPE = '<str:type>'
        def type(self, type):
            return setPathParams(self.TYPE, type)
    
    docs = Docs()
    
    class Compete():
        COMPID = '<str:compID>'

        def compID(self, compID):
            return setPathParams(self.COMPID, compID)

        INDEXTAB = 'indexTab/<str:tab>'

        def indexTab(self, tab):
            return setPathParams(self.INDEXTAB, tab)

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

        CLAIMXP = 'claimxp/<str:compID>/<str:subID>'

        def claimXP(self, compID, subID):
            return setPathParams(self.CLAIMXP, compID, subID)

        GENERATE_CERTS = 'generatecertificate/<str:compID>'
        def generateCert(self,compID):
            return setPathParams(self.GENERATE_CERTS, compID)

        def certficate(self, resID, userID):
            return setPathParams(self.CERTIFICATE, resID, userID)

        CERTIFICATE = 'certificate/<str:resID>/<str:userID>'

        def certficate(self, resID, userID):
            return setPathParams(self.CERTIFICATE, resID, userID)

        CERTDOWNLOAD = 'certificate/download/<str:resID>/<str:userID>'

        def certficateDownload(self, resID, userID):
            return setPathParams(self.CERTDOWNLOAD, resID, userID)

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

        NEWBIES = 'newbies'

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

        ALLLICENSES = 'licenses'

        LICENSE = 'licenses/<str:id>'

        def license(self, id):
            return setPathParams(self.LICENSE, id)

        LICENSES = 'alllicenses'

        ADDLICENSE = 'addlicense'

        CREATEVALIDATEFIELD = 'create/validate/<str:field>'

        def createValidField(self, field):
            return setPathParams(self.CREATEVALIDATEFIELD, field)

        CREATE = 'create'

        def create(self, step: int = 0):
            return f"{self.CREATE}?step={step}"

        SUBMIT = 'submit'

        TRASH = 'trash/<str:projID>'

        def trash(self, projID):
            return setPathParams(self.TRASH, projID)

        PROFILE = 'profile/<str:reponame>'

        def profile(self, reponame):
            return setPathParams(self.PROFILE, reponame)

        PROFILEEDIT = 'profile/edit/<str:projectID>/<str:section>'

        def profileEdit(self, projectID, section):
            return setPathParams(self.PROFILEEDIT, projectID, section)

        TOPICSEARCH = "topics/search/<str:projID>"

        def topicsSearch(self, projID):
            return setPathParams(self.TOPICSEARCH, projID)
        TOPICSUPDATE = "topics/update/<str:projID>"

        def topicsUpdate(self, projID):
            return setPathParams(self.TOPICSUPDATE, projID)

        TAGSEARCH = "tags/search/<str:projID>"

        def tagsSearch(self, projID):
            return setPathParams(self.TAGSEARCH, projID)
        TAGSUPDATE = "tags/update/<str:projID>"

        def tagsUpdate(self, projID):
            return setPathParams(self.TAGSUPDATE, projID)

        LIVEDATA = 'livedata/<str:projID>'

        def liveData(self, projectID):
            return setPathParams(self.LIVEDATA, projectID)

        GITHUB_EVENTS = 'github-events/<str:type>/<str:event>/<str:projID>'

        def githubEvents(self, type, event, projID):
            return setPathParams(self.GITHUB_EVENTS, type, event, projID)

        NEWBIES = 'newbies'

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
        TOPICSEARCH = 'topicsearch'
        JUDGESEARCH = 'judgesearch'
        MODSEARCH = 'moderatorsearch'

        REPORT_FEED = 'report-feedback'
        REPORTS = 'report-feedback/reports'
        CREATE_REPORT = 'report-feedback/reports/create'
        REPORT = 'report-feedback/reports/<str:reportID>'
        FEEDBACKS = 'report-feedback/feedbacks'
        CREATE_FEED = 'report-feedback/feedbacks/create'
        FEEDBACK = 'report-feedback/feedbacks/<str:feedID>'


        COMMUNITY = 'community'
        MODERATORS = 'community/moderators'
        LABELS = 'community/labels'
        LABEL = 'community/labels/<str:type>/<str:labelID>'
        LABEL_TOPICS = 'community/labels/topics'
        LABEL_CATEGORYS = 'community/labels/categories'

        def competition(self, compID):
            return setPathParams(self.COMPETITION,compID)

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
    MANIFEST_JSON = "manifest.json"

    INDEX = 'index'

    @property
    def index(self):
        return f'{self.INDEX}.html'

    OFFLINE = 'offline'
    @property
    def offline(self):
        return f'{self.OFFLINE}.html'

    FORWARD = 'forward'
    @property
    def forward(self):
        return f'{self.FORWARD}.html'

    LANDING = 'landing'
    @property
    def landing(self):
        return f'{self.LANDING}.html'

    INVITATION = 'invitation'
    @property
    def invitation(self):
        return f'{self.INVITATION}.html'
    
    class Auth():
        DIRNAME = 'account'

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
        @property
        def index(self):
            return f'{self.DIRNAME}/{self.INDEX}.html'

        ACTIVE = "index/active"
        @property
        def active(self):
            return f'{self.DIRNAME}/{self.ACTIVE}.html'

        UPCOMING = "index/upcoming"
        @property
        def upcoming(self):
            return f'{self.DIRNAME}/{self.UPCOMING}.html'

        HISTORY = "index/history"
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

        CERTIFICATE = 'certificate'
        @property
        def certificate(self):
            return f'{self.DIRNAME}/{self.CERTIFICATE}.html'

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

        BROWSE_NEWBIE = 'browse/newbie'
        @property
        def browse_newbie(self):
            return f'{self.DIRNAME}/{self.BROWSE_NEWBIE}.html'
        
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

        PROFILE = 'profile'
        @property
        def profile(self):
            return f'{self.DIRNAME}/{self.PROFILE}.html'

        CREATE = 'create'
        @property
        def create(self):
            return f'{self.DIRNAME}/{self.CREATE}.html'

        LICENSE_INDEX = 'license/index'
        @property
        def license_index(self):
            return f'{self.DIRNAME}/{self.LICENSE_INDEX}.html'

        LICENSE_LIC = 'license/license'
        @property
        def license_lic(self):
            return f'{self.DIRNAME}/{self.LICENSE_LIC}.html'

        BROWSE_NEWBIE = 'browse/newbie'
        @property
        def browse_newbie(self):
            return f'{self.DIRNAME}/{self.BROWSE_NEWBIE}.html'

    projects = Projects()

    class Management():
        DIRNAME = MANAGEMENT

    management = Management()


template = Template()

from .methods import classAttrsToDict