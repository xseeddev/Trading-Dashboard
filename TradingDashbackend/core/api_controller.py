from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.utils.order_exec import new_trade_exec
from TradingDashbackend.core.utils.order_exec import exit_trade_exec

from TradingDashbackend.core.utils.trade_user import TradeUser

logger = setup_logger("API Req/Res Controller")

def recieve_request(inputparams):
    # inputparams = [{
    #     "req_id": req_id,
    #     "auth_key":auth_key,
    #     "req_type": req_type,
    #     "req": {}
    # }]

    # if(!is_correct_auth_key(inputparams['auth_key'])):
    #     return "Status: Request Failure, Message: Auth Failure"

    if(inputparams['req_type']=="getLog"):
        return get_user_log()
    elif(inputparams['req_type']=="executeTask"):
        return 

    return "Status: Request Failure, Message: Invalid Request"


def get_user_log():

    return "LOG"

def process_trade_request(inputparams):
    # inputparams = [{
    #     "auth_key":auth_key,
    #     "task": trade_task, #'NEW_TRADE', 'TRADE_EXIT', 'AUTO_TRADE_EXIT'
    #     "user_list": {}
    #     "trade_params":{}
    # }]
    
    # if(!is_correct_auth_key(inputparams['auth_key'])):
    #     return "Status: Request Failure, Message: Auth Failure"

    if(inputparams['task'] not in ['NEW_TRADE', 'TRADE_EXIT', 'AUTO_TRADE_EXIT']):
        return "Status: Request Failure, Message: Invalid Trade Request"
    
    TradeTask = inputparams['task']
    TradeUserList = inputparams['user_list'] #List containing Angel_objs
    TradeParams = inputparams['trade_params']

    if(TradeTask == "NEW_TRADE"):
        for user in TradeUserList:
            params = [{
                "angel_obj":user.angel_obj,
                "client":user.Name,
                "buy_strike":TradeParams['buy_strike'],
                "sell_strike":TradeParams['sell_strike'],
                "option_type":TradeParams['option_type'],
                "expiry":TradeParams['expiry_perf']
            }]
            new_trade_exec(params)
            return None
    elif(TradeTask == "TRADE_EXIT"):
        for user in TradeUserList:
            # order_exit
            inputparams = [{
                "angel_obj":user.angel_obj,
                "client":user.Name,
            }]
            exit_trade_exec(inputparams)
            return
    elif(TradeTask == "AUTO_TRADE_EXIT"):
        for TRADE_USER in TradeUserList:
            # auto_order_exit
            return
    else:
        return "Status: Request Failure, Message: Invalid Trade Request"
