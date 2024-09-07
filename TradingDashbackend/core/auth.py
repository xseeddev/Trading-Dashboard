import datetime
from datetime import timezone
from hashlib import sha256
from TradingDashbackend.core.logger import setup_logger
import json
from requests import request
import jwt
from django.http import JsonResponse

logger = setup_logger("Core:Auth")

# Load configuration from app_config.json
with open('TradingDashbackend/core/app_config.json', 'r') as config_file:
    config = json.load(config_file)

# PASSWORD = sha256(b'sudip').hexdigest()
PASSWORD = "sudip"
JWT_SECRET = 'secret'

def is_correct_user_token(token):   
    try:
        jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={"verify_exp": True})
        logger.debug("Login Success",token)
        return True
    except jwt.ExpiredSignatureError:
        logger.debug("Login Failure",token)
        return False
    except jwt.InvalidTokenError:
        logger.debug("Login Failure",token)
        return False

def portal_validate_login(request):
    password = request['password']
    token = jwt.encode(
        {'password': password, 
         'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=10)}, 
         JWT_SECRET, 
         algorithm='HS256')
    if password == PASSWORD:
        return JsonResponse({"success": True, 'token': token})
    else:
        return JsonResponse({"success": False})

def is_login_request_valid(request):
    try:
        if(len(request.POST)==0):
            return False
        username = request.POST['username']
        password = request.POST['password']
        return True
    except:
        return False

def is_exec_request_valid(request):
    try:
        if(len(request.POST)==0):
            return False
        req_id = request.POST['req_id']
        auth_key = request.POST['auth_key']
        return True
    except:
        return False