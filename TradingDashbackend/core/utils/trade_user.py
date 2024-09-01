from TradingDashbackend.core.utils.api_login import angel_login

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

    def get_angel_obj(self):
        return self.angel_obj
    
    def set_angel_obj(self,angel_obj):
        self.angel_obj = angel_obj
    
    def angel_api_login(self):
        params = [{
            "name":self.name,
            "user_id":self.user_id,
            "password":self.password,
            "api_key":self.api_key,
            "secret_key":self.secret_key,
        }]

        response = angel_login(params)
        self.angel_obj = None

        if(response['status']==True):
            self.angel_obj = response['obj']
        
        return self.angel_obj


