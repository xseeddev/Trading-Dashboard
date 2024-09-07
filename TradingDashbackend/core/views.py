from django.shortcuts import render
from TradingDashbackend.core.logger import setup_logger
from django.views.decorators.csrf import csrf_exempt
from TradingDashbackend.core.auth import is_login_request_valid
from TradingDashbackend.core.auth import is_exec_request_valid
from TradingDashbackend.core.auth import portal_validate_login
from TradingDashbackend.core.api_controller import recieve_request 
logg = setup_logger("Core:Views")

@csrf_exempt
def index(request):
    
    context = {
        "title": "Django example",
    }
    return render(request, "index.html", context)

@csrf_exempt 
def portal_login(request):
    # print("DEB",request)
    print("DEB",request.POST)

    if(is_login_request_valid(request)):
        return portal_validate_login(request.POST)

    return render(request, "index.html")

@csrf_exempt 
def portal_exec(request):
    # print("DEB",request)
    print("DEB-exec",request.POST)
    if(is_exec_request_valid(request)):
        return recieve_request(request.POST)

    return render(request, "index.html")