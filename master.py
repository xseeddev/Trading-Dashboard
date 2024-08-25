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

now = datetime.now()
file_lock = threading.Lock()
reset_event = threading.Event()

def func(client, user_id, password, api_key, secret_key, read_counter, total_clients, read_threads):
    try:
        log_status, angel = api_login.login(3, client, user_id, password, api_key, secret_key)
        sleep(5)

        if log_status == "pass":
            Utils.write_log(client + ": login successfull")
            pause.until(datetime(now.year,now.month,now.day, 9, 15))
            thread_id = threading.get_ident()
            while True:
                try:
                    if (datetime.now().second % 2 == 0):
                        if datetime.now() > datetime(now.year,now.month,now.day, 15, 30):
                            break
                        else:
                            with file_lock:
                                trade_data = json.loads(open(r'C:\algo\backend\trade_attributes.json', 'r').read().rstrip())
                                if trade_data['trade_operation'] not in ['NEW_TRADE', 'TRADE_EXIT', 'AUTO_TRADE_EXIT']:
                                    continue
                                if thread_id in read_threads:
                                    continue
                                read_threads.append(thread_id)

                            if trade_data['trade_operation'] == 'NEW_TRADE':
                                order_place.order_exe(angel, client, trade_data['buy_strike'], trade_data['sell_strike'], trade_data['option_type'], trade_data['expiry_pref'])

                            elif trade_data['trade_operation'] == 'TRADE_EXIT':
                                trade_exit.exit_active_legs(angel, client)

                            elif trade_data['trade_operation'] == 'AUTO_TRADE_EXIT':
                                while True:
                                    nf_ltp = Utils.update_nf_ltp(angel)
                                    if nf_ltp != -1:
                                        if trade_data['option_type'] == 'CE':
                                            if nf_ltp > trade_data['nf_sl'] or nf_ltp < trade_data['nf_target']:
                                                trade_exit.exit_active_legs(angel, client)
                                                break
                                        elif trade_data['option_type'] == 'PE':
                                            if nf_ltp < trade_data['nf_sl'] or nf_ltp > trade_data['nf_target']:
                                                trade_exit.exit_active_legs(angel, client)
                                                break
                                    sleep(2)
                                    with file_lock:
                                        trade_data = json.loads(open(r'C:\algo\backend\trade_attributes.json', 'r').read().rstrip())
                                        if trade_data['trade_operation'] != 'AUTO_TRADE_EXIT':
                                            break

                            with read_counter.get_lock():
                                read_counter.value += 1

                            if read_counter.value == total_clients:
                                with file_lock:
                                    trade_data['trade_operation'] = -1
                                    with open(r'C:\algo\backend\trade_attributes.json', 'w') as f:
                                        json.dump(trade_data, f, indent=2)
                                read_counter.value = 0
                                read_threads[:] = []
                                reset_event.set()
                            else:
                                reset_event.wait()
                                reset_event.clear()
                        sleep(1)
                except:
                    Utils.write_log(client + ": main backend loop exe failed")
                    print("\n" + "main backend loop exe failed @ " + datetime.now().strftime("%H:%M:%S"))
                    traceback.print_exc()
                    sleep(1)          
    except:
        Utils.write_log(client + ": main backend exe failed")
        print("\n" + "main backend exe failed @ " + datetime.now().strftime("%H:%M:%S"))
        traceback.print_exc()
        sleep(1)