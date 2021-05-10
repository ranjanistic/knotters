from django.shortcuts import redirect, render, HttpResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def getCurrentUser(request):
    print(request.user)
    if request.method == "POST":
        if request.user.is_authenticated:
            return HttpResponse({"sessionKey":request.session.session_key})
        return HttpResponse({"sessionKey":None})
    return HttpResponse('Forbidden')
