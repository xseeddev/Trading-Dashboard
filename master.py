from multiprocessing import Value, Manager
from datetime import datetime, date
from utils import Utils
from time import sleep
import pandas as pd
import order_place
import trade_exit
import threading
import traceback
import requests
import api_login
import pause
import json
from logger import setup_logger

now = datetime.now()
file_lock = threading.Lock()
reset_event = threading.Event()
logger = setup_logger("Master Code Logger")

def func(client, user_id, password, api_key, secret_key, read_counter, total_clients, read_threads):
    user_data = [{
        "user_id": user_id,
        "password": password,
        "api_key": api_key,
        "secret_key": secret_key,
        "name": client
    }]
    try:
        login_status, angel_obj = api_login.angel_login(user_data)
        sleep(5)

        if login_status == "pass":
            logger.info(client + ": Login Successfull")
            pause.until(datetime(now.year,now.month,now.day, 9, 15))
            thread_id = threading.get_ident()
            while True:
                try:
                    if (datetime.now().second % 2 == 0):
                        if datetime.now() > datetime(now.year,now.month,now.day, 15, 30):
                            break
                        else:
                            with file_lock:
                                trade_data = json.loads(open(r'backend\trade_attributes.json', 'r').read().rstrip())
                                logger.debug("Loading Trade Attributes",trade_data)
                                if trade_data['trade_operation'] not in ['NEW_TRADE', 'TRADE_EXIT', 'AUTO_TRADE_EXIT']:
                                    continue
                                if thread_id in read_threads:
                                    continue
                                read_threads.append(thread_id)

                            if trade_data['trade_operation'] == 'NEW_TRADE':
                                order_place.order_exe(angel_obj, client, trade_data['buy_strike'], trade_data['sell_strike'], trade_data['option_type'], trade_data['expiry_pref'])

                            elif trade_data['trade_operation'] == 'TRADE_EXIT':
                                trade_exit.exit_active_legs(angel_obj, client)

                            elif trade_data['trade_operation'] == 'AUTO_TRADE_EXIT':
                                while True:
                                    nf_ltp = Utils.update_nf_ltp(angel_obj)
                                    if nf_ltp != -1:
                                        if trade_data['option_type'] == 'CE':
                                            if nf_ltp > trade_data['nf_sl'] or nf_ltp < trade_data['nf_target']:
                                                trade_exit.exit_active_legs(angel_obj, client)
                                                break
                                        elif trade_data['option_type'] == 'PE':
                                            if nf_ltp < trade_data['nf_sl'] or nf_ltp > trade_data['nf_target']:
                                                trade_exit.exit_active_legs(angel_obj, client)
                                                break
                                    sleep(2)
                                    with file_lock:
                                        trade_data = json.loads(open(r'backend\trade_attributes.json', 'r').read().rstrip())
                                        if trade_data['trade_operation'] != 'AUTO_TRADE_EXIT':
                                            break

                            with read_counter.get_lock():
                                read_counter.value += 1

                            if read_counter.value == total_clients:
                                with file_lock:
                                    trade_data['trade_operation'] = -1
                                    with open(r'backend\trade_attributes.json', 'w') as f:
                                        json.dump(trade_data, f, indent=2)
                                read_counter.value = 0
                                read_threads[:] = []
                                reset_event.set()
                            else:
                                reset_event.wait()
                                reset_event.clear()
                        sleep(1)
                except:
                    logger.info(client + ": main backend loop exe failed")
                    logger.debug("\n" + "main backend loop exe failed @ " + datetime.now().strftime("%H:%M:%S") + traceback.print_exc())
                    sleep(1)          
    except:
        logger.info(client + ": main backend exe failed")
        logger.debug("\n" + "main backend exe failed @ " + datetime.now().strftime("%H:%M:%S") + traceback.print_exc())
        sleep(1)