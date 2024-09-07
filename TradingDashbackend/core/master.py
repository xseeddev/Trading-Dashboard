import pandas as pd
import json
from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.utils.trade_user import TradeUser
logger = setup_logger("Core Master")
TRADES_DF = pd.DataFrame(columns=['client', 'symbol', 'token', 'buy_date', 'buy_price', 'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl'])
SCRIPTS_MASTER_DF = pd.DataFrame()
USER_OBJ_LIST = []

def setup_params():

    # create users from json
    with open('TradingDashbackend/core/user_data.json',"r") as user_file:
        data = json.load(user_file) 
    for user in data:
        user_info = {
            'user_id': user.get('user_id'),
            'password': user.get('password'),
            'api_key': user.get('api_key'),
            'secret_key': user.get('secret_key'),
            'name': user.get('name')
        }
        logger.info("Parameters are setup")
        USER_OBJ_LIST.append(TradeUser(user_info))
    # print(USER_OBJ_LIST)
    logger.info("Final Users",USER_OBJ_LIST)

    # login users
    # declare trades df
    # fetch scriptmaster
