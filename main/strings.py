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

ENVIRONMENTS = [environment.DEVELOPMENT, environment.TESTING, environment.PRODUCTION]


class URL():
    INDEX = ''
    ACCOUNTS = 'accounts/'
    PROJECTS = f'{PROJECTS}/'
    COMPETE = f'{COMPETE}/'
    PEOPLE = f'{PEOPLE}/'
    MODERATION = f'{MODERATION}/'
    REDIRECTOR = 'redirector/'
    DOCS = 'docs/'
    DOCTYPE = 'docs/<str:type>'
    LANDINGS = 'landing/'
    LANDING = 'landing'

    class Compete():
        INDEXTAB = 'indexTab/<str:tab>'
        COMPETETABSECTION = 'competeTab/<str:compID>/<str:section>'
        COMPID = '<str:compID>'

    class Moderation():
        REJECT = 'reject',
        APPROVE = 'approve',
        DIVISIONID = '<str:division>/<str:id>'

    class People():
        PROFILE = 'profile/<str:userID>'
        PROFILEEDIT = 'profile/edit/<str:section>'
        PROFILETAB = 'profiletab/<str:userID>/<str:section>'
        SETTINGTAB = 'settingtab/<str:section>'

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
    PROJECTSTATES = [code.MODERATION, code.LIVE, code.REJECTED]
    PROJECTSTATESCHOICE = (
        [code.MODERATION, code.MODERATION.capitalize()],
        [code.LIVE, code.LIVE.capitalize()],
        [code.REJECTED, code.REJECTED.capitalize()]
    )


project = Project()


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