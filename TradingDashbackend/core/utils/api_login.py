from SmartApi.smartConnect import SmartConnect
import pyotp
from logger import setup_logger
from django.http import JsonResponse

logger = setup_logger("Core:Utils:Angel API Login")

# Refactor
def angel_login(user_data):

    client = user_data["user_id"]
    user_id = user_data["user_id"]
    password = user_data["password"]
    api_key = user_data["api_key"]
    secret_key = user_data["secret_key"]
    username = user_data["name"]

    try:
        angel_obj = SmartConnect(api_key)
        angel_session = angel_obj.generateSession(user_id, password, pyotp.TOTP(secret_key).now())
        refreshToken = angel_session['data']['refreshToken']
        feedToken = angel_obj.getfeedToken()
        if angel_session['status'] == True:
            logger.info(username + ": Login Success")
            logger.debug(angel_obj.getProfile(refreshToken))
            # print("DEB: Login Success")
            return JsonResponse({"success": True, 'obj': angel_obj})
        
    except:
        logger.info(username + ": Login Failed")
        # print("DEB: Login Failure")
        return JsonResponse({"success": False, 'obj': None})