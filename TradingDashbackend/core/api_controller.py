from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.utils.order_exec import new_trade_exec
from TradingDashbackend.core.utils.order_exec import exit_trade_exec
from TradingDashbackend.core.utils.order_exec import auto_exit_trade_exec
from TradingDashbackend.core.auth import is_correct_user_token
from TradingDashbackend.core.utils.trade_user import TradeUser
from TradingDashbackend.core.logger import get_current_day_info_logs
from TradingDashbackend.core.logger import get_current_day_debug_logs
from django.http import JsonResponse
from TradingDashbackend.core.master import setup_params
from TradingDashbackend.core.utils.trade_utils import update_script_master
from TradingDashbackend.core.master import SCRIPTS_MASTER_DF

logger = setup_logger("API Req/Res Controller")

def recieve_request(inputparams):
    # inputparams = [{
    #     "req_id": req_id,
    #     "auth_key":auth_key,
    #     "req_type": req_type,
    #     "req": {}
    # }]

    if(not is_correct_user_token(inputparams['auth_key'])):
        resp = {
            "req_id": inputparams['req_id'],
            "success":False,
            "Status": "Request Failure",
            "message": "Auth Failure",
        }
        return JsonResponse(resp, status=200)

    # ---------------- User Validated ---------------- 
    if(inputparams['req_type']=="getLog"):
        log = get_current_day_info_logs() + get_current_day_debug_logs()
        resp = {
            "req_id": inputparams['req_id'],
            "success":True,
            "Status": "Request Success",
            "message": log,
        }
        return JsonResponse(resp, status=200)
    
    elif(inputparams['req_type']=="executeTask"):
        resp = {
            "req_id": inputparams['req_id'],
            "success":True,
            "Status": "Request Success",
            "message": "MEssage",
        }
        return 
    

    elif(inputparams['req_type']=="setupParams"):
        setup_params()
        resp = {
            "req_id": inputparams['req_id'],
            "success":True,
            "Status": "Request Success",
            "message": "Parameter Setup",
        }
        return JsonResponse(resp, status=200)
    
    elif(inputparams['req_type']=="updateScriptMaster"):
        update_script_master()
        resp = {
            "req_id": inputparams['req_id'],
            "success":True,
            "Status": "Request Success",
            "message": ["Script Master Updated",
                        SCRIPTS_MASTER_DF],
        }
        return JsonResponse(resp, status=200)
    elif(inputparams['req_type']=="getScriptMaster"):
        update_script_master()
        resp = {
            "req_id": inputparams['req_id'],
            "success":True,
            "Status": "Request Success",
            "message": ["Script Master:",
                        SCRIPTS_MASTER_DF],
        }
        return JsonResponse(resp, status=200)


    # No Request type Matched
    resp = {
        "req_id": inputparams['req_id'],
        "success":False,
        "Status": "Request Failure",
        "message": "Invalid Request",
    }
    return JsonResponse(resp, status=401)

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
        resp = {
            "req_id": inputparams['req_id'],
            "success":False,
            "Status": "Request Failure",
            "message": "Invalid Trade Request",
        }
        return resp
    
    TradeTask = inputparams['task']
    TradeUserList = inputparams['user_list'] #List containing Angel_objs
    TradeParams = inputparams['trade_params']

    if(TradeTask == "NEW_TRADE"):
        for user in TradeUserList:
            params = [{
                "user_obj":user,
                "Client Name":user.Name,
                "buy_strike":TradeParams['buy_strike'],
                "sell_strike":TradeParams['sell_strike'],
                "option_type":TradeParams['option_type'],
                "expiry":TradeParams['expiry_perf']
            }]
            new_trade_exec(params)

            resp = {
                "req_id": inputparams['req_id'],
                "success":False,
                "Status": "Request Failure",
                "message": "Invalid Trade Request",
            }
            return None
    elif(TradeTask == "TRADE_EXIT"):
        for user in TradeUserList:
            # order_exit
            params = [{
                "angel_obj":user.angel_obj,
                "client":user.Name,
            }]
            exit_trade_exec(params)
            return None
    elif(TradeTask == "AUTO_TRADE_EXIT"):
        for user in TradeUserList:
            # auto_order_exit
            params = [{
                "angel_obj":user.angel_obj,
                "client":user.Name,
                "trade_params":TradeParams
            }]
    
            auto_exit_trade_exec(params)
            return None
    else:
        return "Status: Request Failure, Message: Invalid Trade Request"
