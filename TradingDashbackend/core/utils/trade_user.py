from TradingDashbackend.core.utils.api_login import angel_login
from SmartApi.smartConnect import SmartConnect
from TradingDashbackend.core.logger import setup_logger
import pyotp
import time
import pandas as pd

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
                logger.info(self.Name + ": Login Success")
                logger.debug(self.angel_obj.getProfile(refreshToken))
                resp = [{
                    "success":True,
                    "Status": "Login Success",
                    "message": "Angel API Logged In Successfully",
                }]
                return resp
        except:
                logger.info(self.Name + ": Login Failure")
                resp = [{
                    "success":False,
                    "Status": "Login Failure",
                    "message": "Angel API Login Issue",
                }]
                return resp
        return None

    def available_margin(self):
        try:
            margin = self.angel_obj.rmsLimit()['data']
            # Extracting and converting margin values to integers
            net_margin = int(float(margin.get('net', 0)))
            return net_margin
        except KeyError as e:
            raise ValueError(f"Key error: {e} - Check the structure of the API response.")
        except Exception as e:
            raise RuntimeError(f"An error occurred while fetching the available margin: {e}")

    def req_margin(self, buy_leg_token, sell_leg_token):

        # Sample request data
        data = {
            "positions": [
                {
                    "exchange": "NFO",
                    "qty": 25,
                    "price": 0,
                    "productType": "CARRYFORWARD",
                    "token": buy_leg_token,
                    "tradeType": "BUY"
                },
                {
                    "exchange": "NFO",
                    "qty": 25,
                    "price": 0,
                    "productType": "CARRYFORWARD",
                    "token": sell_leg_token,
                    "tradeType": "SELL"
                }
            ]
        }
        response = self.angel_obj.getMarginApi(data)
        margin_req = int(response['data']['totalMarginRequired'])
        new_margin_req = int(margin_req+(margin_req * 0.20))
        return new_margin_req

    def update_nf_ltp(self, i=[0]):
        try:
            nf_cmp = self.angel_obj.ltpData("NSE", "Nifty 50", "99926000")['data']['ltp']
            i[0] = 0  # Reset i to 0
            return nf_cmp
        except:
            i[0] += 1
            if i[0] > 2:
                logger.debug("nf_ltp_update failed")
                i[0] = 0  # Reset i to 0
            return -1

    def update_positions(self):
        try:
            position = self.angel_obj.position()
            if not position['data']:
                logger.info("No positions found.")
                return
            
            position_df = pd.DataFrame(position['data'])
            columns_to_keep = ['tradingsymbol', 'netqty', 'totalbuyavgprice', 'totalsellavgprice', 'pnl']
            position_df = position_df[columns_to_keep]
            
            message = "Positions:\n"
            for _, row in position_df.iterrows():
                message += f"Symbol: {row['tradingsymbol']}\n"
                message += f"Quantity: {row['netqty']}\n"
                message += f"Buy Price: {row['totalbuyavgprice']}\n"
                message += f"Sell Price: {row['totalsellavgprice']}\n"
                message += f"P&L: {row['pnl']}\n\n"
            logger.info(message)
        
        except Exception as e:
            logger.debug(f"Failed to update positions: {e}")

    def update_holding(self):
        try:
            holding = self.angel_obj.holding()
            if not holding['data']:
                logger.info("No holdings found.")
                return
            
            holding_df = pd.DataFrame(holding['data'])
            columns_to_keep = ['tradingsymbol', 'quantity', 'averageprice', 'profitandloss', 'pnlpercentage']
            holding_df = holding_df[columns_to_keep]
            
            message = "Holdings:\n"
            for _, row in holding_df.iterrows():
                message += f"Symbol: {row['tradingsymbol']}\n"
                message += f"Quantity: {row['quantity']}\n"
                message += f"Avg Price: {row['averageprice']}\n"
                message += f"P&L: {row['profitandloss']}\n"
                message += f"P&L %: {row['pnlpercentage']}\n\n"
            logger.info(message)
        
        except Exception as e:
            logger.debug(f"Failed to update holdings: {e}")


    def get_ltp(self, token, symbol, max_retries=6, retry_delay=2):
        attempt = 0
        while attempt < max_retries:
            try:
                ltp_data = self.angel_obj.ltpData("NFO", symbol, token)
                ltp = ltp_data['data']['ltp']
                return ltp
            except Exception as e:
                logger.debug(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(retry_delay)
        
        logger.debug("Max retries reached. LTP update failed.")
        return None

    def update_nifty_ltp(self, max_retries=2, retry_delay=1):
        attempt = 0

        while attempt < max_retries:
            try:
                # Fetch the LTP data for Nifty 50
                nf_cmp = self.angel_obj.ltpData("NSE", "Nifty 50", "99926000")['data']['ltp']
                return nf_cmp
            except Exception as e:
                # Log the error and increment the attempt counter
                logger.debug(f"Attempt {attempt + 1} failed: {e}")
                attempt += 1
                time.sleep(retry_delay)
        
        # After max retries, log failure and return -1
        logger.debug("Max retries reached. Nifty LTP update failed.")
        return -1