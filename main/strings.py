from projects.apps import APPNAME as PROJECTS
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE
from moderation.apps import APPNAME as MODERATION

DIVISIONS = [PROJECTS, PEOPLE, COMPETE, MODERATION]


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
