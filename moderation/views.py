from django.http.response import Http404, HttpResponse,HttpResponseBadRequest
from main.renderer import renderView
from people.models import User
from project import *
from compete import *
from people import *
from .models import *

DIVISIONS = ['people','project','competition']

def moderation(request,division,id):
    if not DIVISIONS.__contains__(division):
        raise Http404()
    else:
        return HttpResponse(f"{division} moderation for {id}")

# implemented round robin algorithm
def getModerator():
    try:
        current = localStorage.objects.get(key="moderator")
    except:
        current = localStorage.objects.create(key="moderator",value=0)
        current.save()
    
    totalModerators = User.objects.filter(is_moderator=True)
    if(totalModerators.count==0):
        print("No moderators exist")
        return HttpResponseBadRequest(content="No moderator exist in system")
    temp = int(current.value)
    if(temp>=totalModerators.count()):
        temp = 1
    else:
        temp = temp+1
    current.value = temp
    current.save()
    print(totalModerators[temp-1])
    return totalModerators[temp-1]



def requestModeration(id,type,userinput):
    try:
        if(type=="project"):
            obj = moderation.objects.get(project_id=id)
        elif(type=="people"):
            obj = moderation.objects.get(user_id=id)
        else:
            obj = moderation.objects.get(competiton_id=id)
        return False
    except:
        moderator = getModerator()
        if(type=="project"):
            obj = moderation.objects.create(project_id=id,type=type,moderator=moderator,request=userinput)
        elif(type=="people"):
            obj = moderation.objects.create(user_id=id,type=type,moderator=moderator,request=userinput)
        else:
            obj = moderation.objects.create(competiton_id=id,type=type,moderator=moderator,request=userinput)
        obj.save()
    return True


def disapprove(request):
    if(request.method=="POST"):
        id = request.POST["id"]
        reason  = request.POST["reason"]
        obj = moderation.objects.get(id=id)
        obj.reject(reason)
        return HttpResponse("Rejection success")

