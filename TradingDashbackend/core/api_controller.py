from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.utils.order_exec import new_trade_exec

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
    
    TRADE_TASK = inputparams['task']
    TRADE_USER_LIST = inputparams['user_list'] #List containing Angel_objs
    TRADE_PARAMS = inputparams['trade_params']

    if(TRADE_TASK == "NEW_TRADE"):
        for TRADE_USER in TRADE_USER_LIST:
            # (angel_obj, client, trade_data['buy_strike'], trade_data['sell_strike'], trade_data['option_type'], trade_data['expiry_pref'])
            params = [{
                "angel_obj":TRADE_USER,
                "client":TRADE_USER,
                "buy_strike":TRADE_PARAMS['buy_strike'],
                "sell_strike":TRADE_PARAMS['sell_strike'],
                "option_type":TRADE_PARAMS['option_type'],
                "expiry":TRADE_PARAMS['expiry']
            }]
            new_trade_exec(params)
            return
    elif(TRADE_TASK == "TRADE_EXIT"):
        for TRADE_USER in TRADE_USER_LIST:
            # order_exit
            return
    elif(TRADE_TASK == "AUTO_TRADE_EXIT"):
        for TRADE_USER in TRADE_USER_LIST:
            # auto_order_exit
            return
    else:
        return "Status: Request Failure, Message: Invalid Trade Request"
