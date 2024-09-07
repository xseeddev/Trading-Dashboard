from TradingDashbackend.core.utils.api_login import angel_login
from SmartApi.smartConnect import SmartConnect
from TradingDashbackend.core.logger import setup_logger
import pyotp

logger = setup_logger("Core:Trade User")

class TradeUser:
    Name = "Default"
    user_id = "#000000"
    password = "#000000"
    api_key = "ABCDE12345"
    secret_key = "ABCDE12345"
    angel_obj = None

    def __init__(self,name,user_id,password,api_key,secret_key):
        self.Name = name
        self.user_id = user_id
        self.password = password
        self.api_key = api_key
        self.secret_key = secret_key
    
    def __init__(self,json_obj):
        self.Name = json_obj['name']
        self.user_id = json_obj['user_id']
        self.password = json_obj['password']
        self.api_key = json_obj['api_key']
        self.secret_key = json_obj['secret_key']
    
    def get_angel_obj(self):
        return self.angel_obj
    
    def set_angel_obj(self,angel_obj):
        self.angel_obj = angel_obj
    
    def angel_api_login(self):
        # params = [{
        #     "name":self.name,
        #     "user_id":self.user_id,
        #     "password":self.password,
        #     "api_key":self.api_key,
        #     "secret_key":self.secret_key,
        # }]

        # response = angel_login(params)
        try:
            self.angel_obj = SmartConnect(self.api_key)
            angel_session = self.angel_obj.generateSession(self.user_id, self.password, pyotp.TOTP(self.secret_key).now())
            refreshToken = angel_session['data']['refreshToken']
            feedToken = self.angel_obj.getfeedToken()
            if angel_session['status'] == True:
                logger.info(self.username + ": Login Success")
                logger.debug(self.angel_obj.getProfile(refreshToken))
                resp = [{
                    "success":True,
                    "Status": "Login Success",
                    "message": "Angel API Logged In Successfully",
                }]
                return resp
        except:
                logger.info(self.username + ": Login Failure")
                resp = [{
                    "success":False,
                    "Status": "Login Failure",
                    "message": "Angel API Login Issue",
                }]
                return resp
        return None


