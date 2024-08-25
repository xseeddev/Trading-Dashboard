from SmartApi.smartConnect import SmartConnect
from datetime import datetime, date
from utils import Utils
from time import sleep
import traceback
import pyotp
import json

def login(logincount, client, user_id, password, api_key, secret_key):
    if logincount==0:
       return "fail", None
    else:
        try:
            angel = SmartConnect(api_key)
            data = angel.generateSession(user_id, password, pyotp.TOTP(secret_key).now())
            refreshToken = data['data']['refreshToken']
            feedToken = angel.getfeedToken()
            if data['status'] == True:
                print(angel.getProfile(refreshToken))
                return "pass", angel
        except:
            logincount = logincount - 1
            Utils.write_log(client + ": login failed")
            print("\n" + client+ ": login failed @ " + datetime.now().strftime("%H:%M:%S"))
            traceback.print_exc()
            sleep(5)
            return login(logincount)

# Refactor
def angel_login(user_data):
    
    user_id = user_data["user_id"]
    password = user_data["user_id"]
    api_key = user_data["api_key"]
    secret_key = user_data["secret_key"]
    username = user_data["name"]

    try:
        angel_obj = SmartConnect(api_key)
        angel_session = angel_obj.generateSession(user_id,password,pyotp.TOTP(secret_key).now())
        refreshToken = angel_session['data']['refreshToken']
        if angel_session['status'] == True:
            Utils.write_log(username + ": Login Success")
            Utils.write_log(angel_obj.getProfile(refreshToken))
            return "Status:Login Success",angel_obj
    except:
        Utils.write_log(username + ": Login Failed")
        return "Status:Login Fail",None