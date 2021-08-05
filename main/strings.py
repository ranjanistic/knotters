import re
from projects.apps import APPNAME as PROJECTS
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE
from moderation.apps import APPNAME as MODERATION


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

    class Test():
        MODEL = 'model'
        VIEW = 'view'
        METHOD = 'method'
        STATIC = 'static'


code = Code()


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



setPathParams('asf')


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

DIVISIONS = [PROJECTS, PEOPLE, COMPETE, MODERATION]


class URL():
    INDEX = ''
    FAVICON = 'favicon.ico'
    ROBOTS_TXT = 'robots.txt'
    MANIFEST = 'manifest.json'
    SERVICE_WORKER = 'service-worker.js'
    OFFLINE = 'off408'
    ACCOUNTS = "auth/"
    ROOT = '/'
    PROJECTS = f'{PROJECTS}/'
    COMPETE = f'{COMPETE}/'
    PEOPLE = f'{PEOPLE}/'
    MODERATION = f'{MODERATION}/'
    REDIRECTOR = 'redirector/'
    DOCS = 'docs/'
    DOCTYPE = 'docs/<str:type>'
    LANDINGS = 'landing/'
    LANDING = 'landing'
    APPLANDING = '<str:subapp>/landing'

    REPORT_FEEDBACK = 'report-feedback'

    def getRoot(self, fromApp: str = '') -> str:
        """
        Returns root path of given sub application name.

        :fromApp: The app name, if nothing or invalid value is passed, returns root.
        """
        if fromApp == COMPETE:
            return f"/{self.COMPETE}"
        elif fromApp == PROJECTS:
            return f"/{self.PROJECTS}"
        elif fromApp == PEOPLE:
            return f"/{self.PEOPLE}"
        elif fromApp == MODERATION:
            return f"/{self.MODERATION}"
        else:
            return self.ROOT

    def getMessageQuery(self, alert: str = '', error: str = '', success: str = '', otherQueries:bool=False) -> str:
        if error:
            error = f"{'&' if otherQueries else '?'}e={error}" if message.isValid(error) else ''
            otherQueries = message.isValid(error)
        if alert:
            alert = f"{'&' if otherQueries else '?' }a={alert}" if message.isValid(alert) else ''
            otherQueries = message.isValid(alert)
        if success:
            success = f"{'&' if otherQueries else '?'}s={success}" if message.isValid(
                success) else ''
        return f"{error}{alert}{success}"

    def githubProfile(self, ghID):
        return f"https://github.com/{ghID}"

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

        ACCOUNTPREFERENCES = "account/preferences/<str:userID>"

        def accountPreferences(self, userID):
            return setPathParams(self.ACCOUNTPREFERENCES, userID)

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
        def create(self,step:int=0):
            return f"{self.CREATE}?step={step}"

        SUBMIT = 'submit'

        TRASH = 'trash/<str:projID>'

        def trash(self,projID):
            return setPathParams(self.TRASH,projID)

        PROFILE = 'profile/<str:reponame>'

        def profile(self, reponame):
            return setPathParams(self.PROFILE, reponame)

        PROFILEEDIT = 'profile/edit/<str:projectID>/<str:section>'

        def profileEdit(self, projectID, section):
            return setPathParams(self.PROFILEEDIT, projectID, section)

        TOPICSEARCH = "topics/search/<str:projID>"
        def topicsSearch(self,projID):
            return setPathParams(self.TOPICSEARCH,projID)
        TOPICSUPDATE = "topics/update/<str:projID>"
        def topicsUpdate(self,projID):
            return setPathParams(self.TOPICSUPDATE,projID)

        TAGSEARCH = "tags/search/<str:projID>"
        def tagsSearch(self,projID):
            return setPathParams(self.TAGSEARCH,projID)
        TAGSUPDATE = "tags/update/<str:projID>"
        def tagsUpdate(self,projID):
            return setPathParams(self.TAGSUPDATE,projID)

        PROJECTINFO = 'projectinfo/<str:projectID>/<str:info>'

        def projectInfo(self, projectID, info):
            return setPathParams(self.PROJECTINFO, projectID, info)

        def getURLSForClient(self):
            URLS = dict()

            def cond(key, value):
                return str(key).isupper()
            urls = classAttrsToDict(URL.Projects, cond)

            for key in urls:
                URLS[key] = f"{url.getRoot(PROJECTS)}{setPathParams(urls[key])}"
            return URLS

    projects = Projects()

    def getURLSForClient(self) -> dict:
        URLS = dict()

        def cond(key, value):
            return str(key).isupper()
        urls = classAttrsToDict(URL, cond)

        for key in urls:
            URLS[key] = f"{url.getRoot() if urls[key] != url.getRoot() else ''}{setPathParams(urls[key])}"
        return URLS

url = URL()

class Project():
    PROJECTSTATES = [code.MODERATION, code.APPROVED, code.REJECTED]
    PROJECTSTATESCHOICES = (
        [code.MODERATION, code.MODERATION.capitalize()],
        [code.APPROVED, code.APPROVED.capitalize()],
        [code.REJECTED, code.REJECTED.capitalize()]
    )


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
    CONTRIBUTION = "contribution"
    ACTIVITY = "activity"
    MODERATION = "moderation"

    class Setting():
        ACCOUNT = "account"
        PREFERENCE = "preference"

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

from main.methods import classAttrsToDict