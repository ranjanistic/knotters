from project.apps import APPNAME as PROJECT
from people.apps import APPNAME as PEOPLE
from compete.apps import APPNAME as COMPETE

DIVISIONS = [PROJECT, PEOPLE, COMPETE]


class Codes():
    OK = "OK"
    NO = "NO"
    APPROVED = 'approved'
    REJECTED = 'rejected'
    LIVE = 'live'
    MODERATION = 'moderation'
    INVALID_DIVISION = f'INVALID_DIVISION'
    SUBMISSION_ERROR = f'{COMPETE}/SUBMISSION_ERROR'
    SUBMISSION_EXISTS = f'{COMPETE}/SUBMISSION_EXISTS'
    
    def __init__(self):
        PROJECTSTATES = [self.MODERATION, self.LIVE, self.REJECTED]

class Profile():
    OVERVIEW = 'overview'
    PROJECTS = 'projects'
    CONTRIBUTION = 'contribution'
    ACTIVITY = 'activity'

profile = Profile()
code = Codes()
