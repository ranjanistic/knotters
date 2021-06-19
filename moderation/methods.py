from people.models import User
from .models import *
from main.methods import renderView
from .apps import APPNAME
from main.strings import PROJECTS, PEOPLE, COMPETE, code


def renderer(request, file, data={}):
    return renderView(request, file, data, fromApp=APPNAME)


# implemented round robin algorithm
def getModerator():
    try:
        current = LocalStorage.objects.get(key="moderator")
    except:
        current = LocalStorage.objects.create(key="moderator", value=0)
        current.save()

    totalModerators = User.objects.filter(is_moderator=True)
    if(totalModerators.count == 0):
        return False
    temp = int(current.value)
    if(temp >= totalModerators.count()):
        temp = 1
    else:
        temp = temp+1
    current.value = temp
    current.save()
    return totalModerators[temp-1]


def requestModeration(projectID, type, userRequest):
    obj = None
    try:
        if(type == PROJECTS):
            obj = Moderation.objects.get(project_id=projectID)
        elif(type == PEOPLE):
            obj = Moderation.objects.get(user_id=projectID)
        elif(type == COMPETE):
            obj = Moderation.objects.get(competiton_id=projectID)

        if obj.status == code.REJECTED and obj.retries > 0:
            obj.status = code.MODERATION
            obj.moderator = getModerator()

            if type == PROJECTS:
                obj.project.status = code.MODERATION
                obj.project.save()
                
            obj.save()
            return True
        
        return False
    except:
        moderator = getModerator()
        if not moderator:
            return False
        if(type == PROJECTS):
            obj = Moderation.objects.create(
                project_id=projectID, type=type, moderator=moderator, request=userRequest)
        elif(type == PEOPLE):
            obj = Moderation.objects.create(
                user_id=projectID, type=type, moderator=moderator, request=userRequest)
        elif(type == COMPETE):
            obj = Moderation.objects.create(
                competiton_id=projectID, type=type, moderator=moderator, request=userRequest)
        obj.save()
    return True
