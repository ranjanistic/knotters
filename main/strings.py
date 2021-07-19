import re
from projects.apps import APPNAME as PROJECTS
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE
from moderation.apps import APPNAME as MODERATION


def setPathParams(path: str, *replacingChars: str) -> str:
    """
    Replaces <str:param> of defined urls with given character (default: *), primarily for dynamic client side service worker.
    """
    i = 0
    while i < len(replacingChars):
        path = re.sub(Code.URLPARAM, str(replacingChars[i]), path, 1)
        i += 1
    return path


class Environment():
    DEVELOPMENT = 'development'
    TESTING = 'testing'
    PRODUCTION = 'production'


environment = Environment()

ENVIRONMENTS = [Environment.DEVELOPMENT,
                Environment.TESTING, Environment.PRODUCTION]


class Code():
    OK = "OK"
    NO = "NO"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODERATION = "moderation"
    INVALID_DIVISION = "INVALID_DIVISION"
    SWASSETS = 'swassets'
    MODERATOR = "moderator"
    ZOMBIE = 'Zombie'
    ZOMBIEMAIL = 'zombie@knotters.org'
    URLPARAM = r'(<str:|<int:)+[a-zA-Z0-9]+(>)'

code = Code()

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

    ACCOUNT_DELETED = "Account deleted successfully."

    def isValid(self, message: str) -> bool:
        """
        Whether the given string is a valid message response to be sent to client or not. This check will ensure that
        malicious messages as url query alert/error are not being shown to someone via any url of this application.

        This requires that all response messages should be an attribute of this Message class.

        :message: The message string to be checked for validity.
        """
        return [
            self.ERROR_OCCURRED,
            self.INVALID_REQUEST,
            self.INVALID_RESPONSE,
            self.SAVED,

            self.RESULT_DECLARED,
            self.ALREADY_PARTICIPATING,
            self.PARTICIPATION_WITHDRAWN,
            self.MEMBER_REMOVED,
            self.INVALID_ID,
            self.USER_NOT_EXIST,
            self.USER_PARTICIPANT_OR_INVITED,
            self.SUBMITTED_ALREADY,
            self.SUBMITTED_SUCCESS,
            self.SUBMITTED_LATE,
            self.SUBMISSION_TOO_LATE,
            self.SUBMISSION_MARKING_INVALID,
            self.SUBMISSION_ERROR,

            self.SENT_FOR_REVIEW,
            self.PROJECT_DELETED,
            self.TERMS_UNACCEPTED,

            self.ALREADY_RESOLVED,
            self.REQ_MESSAGE_SAVED,
            self.RES_MESSAGE_SAVED,
            self.MODERATION_REAPPLIED,

            self.ACCOUNT_PREF_SAVED,
            self.SUCCESSOR_GH_UNLINKED,
            self.SUCCESSOR_OF_PROFILE,
            self.SUCCESSOR_NOT_FOUND,
            self.SUCCESSOR_UNSET,
            self.SUCCESSORSHIP_DECLINED,
            self.SUCCESSORSHIP_ACCEPTED,

            self.ACCOUNT_DELETED
        ].__contains__(message)


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

    def getMessageQuery(self, alert: str = '', error: str = '', success: str = ''):
        if error:
            error = f"?e={error}" if message.isValid(error) else ''
        if alert:
            alert = f"{'&' if error else '?' }a={alert}" if message.isValid(
                alert) else ''
        if success:
            success = f"{'&' if error or alert else '?'}s={success}" if message.isValid(
                success) else ''
        else:
            return ''
        return f"{error}{alert}{success}"

    def githubProfile(self, ghID):
        return f"https://github.com/{ghID}"

    class Compete():
        COMPID = '<str:compID>'

        def compID(self, compID):
            return setPathParams(self.COMPID, compID)

        INDEXTAB = 'indexTab/<str:tab>'
        COMPETETABSECTION = 'competeTab/<str:compID>/<str:section>'
        DATA = "data/<str:compID>"

        PARTICIPATE = 'participate/<str:compID>'

        def participate(self, compID):
            return setPathParams(self.PARTICIPATE, compID)

        REMOVEMEMBER = 'remove/<str:subID>/<str:userID>'
        INVITE = 'invite/<str:subID>'
        INVITATION = 'invitation/<str:subID>/<str:userID>'
        INVITEACTION = 'invitation/<str:subID>/<str:userID>/<str:action>'

        SAVE = 'save/<str:compID>/<str:subID>'

        def save(self, compID, subID):
            return setPathParams(self.SAVE, compID, subID)

        SUBMIT = 'submit/<str:compID>/<str:subID>'

        SUBMITPOINTS = 'submissionpoints/<str:compID>'

        def submitPoints(self, compID):
            return setPathParams(self.SUBMITPOINTS, compID)

        DECLARERESULTS = 'declareresults/<str:compID>'

        def declareResults(self, compID):
            return setPathParams(self.DECLARERESULTS, compID)

    compete = Compete()

    class Moderation():
        MODID = '<str:id>'

        def modID(self, modID):
            return setPathParams(self.MODID, modID)

        MESSAGE = 'message/<str:modID>'
        ACTION = 'action/<str:modID>'

        REAPPLY = 'reapply/<str:modID>'

        def reapply(self, modID):
            return setPathParams(self.REAPPLY, modID)

        APPROVECOMPETE = 'compete/<str:modID>'

        def approveCompete(self, modID):

            return setPathParams(self.APPROVECOMPETE, modID)

    moderation = Moderation()

    class People():
        PROFILE = 'profile/<str:userID>'

        def profile(self, userID):
            return setPathParams(self.PROFILE, userID)

        PROFILEEDIT = 'profile/edit/<str:section>'
        PROFILETAB = 'profiletab/<str:userID>/<str:section>'
        SETTINGTAB = 'settingtab/<str:section>'

        ACCOUNTPREFERENCES = "account/preferences/<str:userID>"

        def accountPreferences(self, userID):
            return setPathParams(self.ACCOUNTPREFERENCES, userID)

        ACCOUNTACTIVATION = "account/activation"
        GETSUCCESSOR = 'account/successor'
        INVITESUCCESSOR = 'account/successor/invite'
        ACCOUNTDELETE = "account/delete"

        SUCCESSORINVITE = 'invitation/successor/<str:predID>'

        def successorInvite(self, predID):
            return setPathParams(self.SUCCESSORINVITE, predID)

        SUCCESSORINVITEACTION = 'invitation/successor/action/<str:action>'

        ZOMBIE = 'zombie/<str:profileID>'

        def zombie(self, profileID):
            return setPathParams(self.ZOMBIE, profileID)

    people = People()

    class Projects():
        CREATEVALIDATEFIELD = 'create/validate/<str:field>'
        CREATE = 'create'
        SUBMIT = 'submit'

        PROFILE = 'profile/<str:reponame>'

        def profile(self, reponame):
            return setPathParams(self.PROFILE, reponame)

        PROFILEEDIT = 'profile/edit/<str:projectID>/<str:section>'
        PROJECTINFO = 'projectinfo/<str:projectID>/<str:info>'

    projects = Projects()

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

    TYPES = DIVISIONS

    TYPECHOICES = ([PROJECTS, PROJECTS.capitalize()], [PEOPLE, PEOPLE.capitalize(
    )], [COMPETE, COMPETE.capitalize()])


moderation = Moderation()


class ProfileSetting():
    ACCOUNT = "account"
    PREFERENCE = "preference"


class Profile():
    OVERVIEW = "overview"
    PROJECTS = "projects"
    CONTRIBUTION = "contribution"
    ACTIVITY = "activity"
    MODERATION = "moderation"
    setting = ProfileSetting()


class Compete():
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
