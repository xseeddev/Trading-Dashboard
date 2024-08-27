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
with open('app_config.json', 'r') as config_file:
    config = json.load(config_file)

PASSWORD = sha256(b'sudip').hexdigest()
JWT_SECRET = 'secret'

def is_token_valid(token):   
    try:
        jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={"verify_exp": True})
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

def check_user_token():
    token = request.headers.get('Authorization')
    if not is_token_valid(token):
        logger.debug("Login Failure",request.json['data']) 
        return JsonResponse({"success": False, "message": "Invalid token"}, status=401)
    logger.debug("Login Success",request.json['data'])
    return JsonResponse({"success": True, "message": "Data written successfully"}, status=200)

def portal_validate_login():
    password = request.json['password']
    token = jwt.encode(
        {'password': password, 
         'exp': datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=1)}, 
         JWT_SECRET, 
         algorithm='HS256')
    if password == PASSWORD:
        return JsonResponse({"success": True, 'token': token})
    else:
        return JsonResponse({"success": False})
