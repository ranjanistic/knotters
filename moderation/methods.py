from people.models import User
from .models import *
from main.methods import renderView
from .apps import APPNAME
from main.strings import PROJECT, PEOPLE, COMPETE, code


def renderer(request, file, data={}):
    data['root'] = f"/{APPNAME}"
    data['subappname'] = APPNAME
    return renderView(request, f"{APPNAME}/{file}", data)


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


def requestModeration(id, type, userRequest):
    obj = None
    try:
        if(type == PROJECT):
            obj = Moderation.objects.get(project_id=id)
        elif(type == PEOPLE):
            obj = Moderation.objects.get(user_id=id)
        elif(type == COMPETE):
            obj = Moderation.objects.get(competiton_id=id)

        if obj.status == code.REJECTED and obj.retries > 0:
            obj.status = code.MODERATION
            obj.moderator = getModerator()
            obj.save()
            return True
        
        return False
    except:
        moderator = getModerator()
        if(type == PROJECT):
            obj = Moderation.objects.create(
                project_id=id, type=type, moderator=moderator, request=userRequest)
        elif(type == PEOPLE):
            obj = Moderation.objects.create(
                user_id=id, type=type, moderator=moderator, request=userRequest)
        elif(type == COMPETE):
            obj = Moderation.objects.create(
                competiton_id=id, type=type, moderator=moderator, request=userRequest)
        obj.save()
    return True
