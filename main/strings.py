from projects.apps import APPNAME as PROJECTS
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE
from moderation.apps import APPNAME as MODERATION

DIVISIONS = [PROJECTS, PEOPLE, COMPETE, MODERATION]


class Environment():
    DEVELOPMENT = 'development'
    TESTING = 'testing'
    PRODUCTION = 'production'


environment = Environment()

ENVIRONMENTS = [environment.DEVELOPMENT,
                environment.TESTING, environment.PRODUCTION]


class URL():
    INDEX = ''
    FAVICON = 'favicon.ico'
    ROBOTS_TXT = 'robots.txt'
    MANIFEST = 'manifest.json'
    SERVICE_WORKER = 'service-worker.js'
    OFFLINE = 'off408'
    ACCOUNTS = "auth/"
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

    class Compete():
        COMPID = '<str:compID>'
        INDEXTAB = 'indexTab/<str:tab>'
        COMPETETABSECTION = 'competeTab/<str:compID>/<str:section>'
        DATA = "data/<str:compID>"
        PARTICIPATE = 'participate/<str:compID>'
        REMOVEMEMBER = 'remove/<str:subID>/<str:userID>'
        INVITE = 'invite/<str:subID>'
        INVITATION = 'invitation/<str:subID>/<str:userID>'
        INVITEACTION = 'invitation/<str:subID>/<str:userID>/<str:action>'
        SAVE = 'save/<str:compID>/<str:subID>'
        SUBMIT = 'submit/<str:compID>/<str:subID>'

        SUBMITPOINTS = 'submissionpoints/<str:compID>'
        DECLARERESULTS = 'declareresults/<str:compID>'

    class Moderation():
        MODID = '<str:id>'
        MESSAGE = 'message/<str:modID>'
        ACTION = 'action/<str:modID>'
        REAPPLY = 'reapply/<str:modID>'
        APPROVECOMPETE = 'compete/<str:modID>'

    class People():
        PROFILE = 'profile/<str:userID>'
        PROFILEEDIT = 'profile/edit/<str:section>'
        PROFILETAB = 'profiletab/<str:userID>/<str:section>'
        SETTINGTAB = 'settingtab/<str:section>'

        ACCOUNTPREFERENCES = "account/preferences/<str:userID>"
        ACCOUNTACTIVATION = "account/activation"
        GETSUCCESSOR = 'account/successor'
        INVITESUCCESSOR = 'account/successor/invite'
        ACCOUNTDELETE = "account/delete"

        SUCCESSORINVITE = 'invitation/successor/<str:predID>'
        SUCCESSORINVITEACTION = 'invitation/successor/action/<str:action>'

        ZOMBIE = 'zombie/<str:profileID>'

    class Projects():
        CREATEVALIDATEFIELD = 'create/validate/<str:field>'
        CREATE = 'create'
        SUBMIT = 'submit'
        PROFILE = 'profile/<str:reponame>'
        PROFILEEDIT = 'profile/edit/<str:projectID>/<str:section>'
        PROJECTINFO = 'projectinfo/<str:projectID>/<str:info>'


url = URL()


class Codes():
    OK = "OK"
    NO = "NO"
    APPROVED = "approved"
    REJECTED = "rejected"
    LIVE = "live"
    MODERATION = "moderation"
    INVALID_DIVISION = "INVALID_DIVISION"
    SUBMISSION_ERROR = f"{COMPETE}/SUBMISSION_ERROR"
    SUBMISSION_EXISTS = f"{COMPETE}/SUBMISSION_EXISTS"


code = Codes()


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
