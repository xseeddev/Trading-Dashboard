'''
    #TODO: Complete this.
'''

#  <---------------------- Angel.py ---------------------->
from datetime import datetime
from utils import Utils
from time import sleep
import traceback
import pause
import json

now = datetime.now()

try:
    if __name__ == "__main__":

        while True:
            i = 0
            now = datetime.now()

            # Check if today is a holiday
            if Utils.IsTodayHoliday():
                i = 1
                # Pause execution until the end of the day (11:58 PM)
                pause.until(datetime(now.year, now.month, now.day, 23, 58))
                sleep(1800)

            if i == 0:
                # Check if the current time is before 8:15 AM, wait until market opens
                if datetime.now() < datetime(now.year, now.month, now.day, 8, 15):
                    print("Market login @ 8:15 AM")
                    pause.until(datetime(now.year, now.month, now.day, 8, 15))

                # Update script master
                Utils.update_script_master()

                # Process client details sequentially
                client_details = json.loads(open('user_zer.json', 'r').read().rstrip())
                total_clients = len(client_details)

                # Process each client in sequence
                for client in client_details:
                    func(
                        client['name'], 
                        client['user_id'], 
                        client['password'], 
                        client['api_key'], 
                        client['secret_key'], 
                        None,  # No need for read_counter now
                        total_clients, 
                        None  # No shared threads list since no multiprocessing
                    )
                    sleep(3)  # Pause between processing each client

                # Delete closed trades after processing all clients
                Utils.delete_closed_trades()

                # Indicate market closing
                print("Market closing bell")
                print("Algo now in sleep mode")

                # Pause until the end of the day (11:58 PM)
                pause.until(datetime(now.year, now.month, now.day, 23, 58))
                sleep(900)

except Exception as e:
    print("Angel execution failed")
    print("\nAngel execution failed @ " + datetime.now().strftime("%H:%M:%S"))
    traceback.print_exc()




# <---------------------- Master.py ---------------------->

from datetime import datetime
from utils import Utils
from time import sleep
import pandas as pd
import order_place
import trade_exit
import traceback
import requests
import login
import pause
import json

now = datetime.now()

def func(client, user_id, password, api_key, secret_key):
    """
    Sequentially executes trade logic for the given client.
    
    Parameters:
    - client: The client name.
    - user_id: The user ID.
    - password: The password.
    - api_key: The API key.
    - secret_key: The secret key.
    
    Returns:
    - None
    """
    try:
        log_status, angel = login.login(3, client, user_id, password, api_key, secret_key)
        sleep(5)

        if log_status == "pass":
            Utils.write_log(f"{client}: login successful")
            pause.until(datetime(now.year, now.month, now.day, 9, 15))

            while True:
                try:
                    # Exit if current time is after 3:30 PM
                    if datetime.now() > datetime(now.year, now.month, now.day, 15, 30):
                        break

                    # Read trade attributes
                    with open(r'C:\algo\backend\trade_attributes.json', 'r') as file:
                        trade_data = json.load(file)
                    
                    # If no valid trade operation is specified, skip to the next iteration
                    if trade_data['trade_operation'] not in ['NEW_TRADE', 'TRADE_EXIT', 'AUTO_TRADE_EXIT']:
                        continue

                    # Execute trade operations based on the trade_operation value
                    if trade_data['trade_operation'] == 'NEW_TRADE':
                        order_place.order_exe(
                            angel, client, 
                            trade_data['buy_strike'], trade_data['sell_strike'], 
                            trade_data['option_type'], trade_data['expiry_pref']
                        )

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

                            # Reload trade data to check if the operation has changed
                            with open(r'C:\algo\backend\trade_attributes.json', 'r') as file:
                                trade_data = json.load(file)
                            if trade_data['trade_operation'] != 'AUTO_TRADE_EXIT':
                                break

                    # Reset trade operation if all clients are processed
                    with open(r'C:\algo\backend\trade_attributes.json', 'w') as file:
                        trade_data['trade_operation'] = -1
                        json.dump(trade_data, file, indent=2)
                    
                    sleep(1)
                except:
                    Utils.write_log(f"{client}: main backend loop execution failed")
                    print(f"\nmain backend loop execution failed @ {datetime.now().strftime('%H:%M:%S')}")
                    traceback.print_exc()
                    sleep(1)
    except:
        Utils.write_log(f"{client}: main backend execution failed")
        print(f"\nmain backend execution failed @ {datetime.now().strftime('%H:%M:%S')}")
        traceback.print_exc()
        sleep(1)
