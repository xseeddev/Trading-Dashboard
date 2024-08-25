from multiprocessing import Value, Manager
from datetime import datetime, date
from utils import Utils
from time import sleep
from master import func
import threading
import traceback
import pause
import json
from logger import setup_logger

logger = setup_logger("Main Trade kernel")

now = datetime.now()

try:
    if __name__ == "__main__":

        while True:
            i=0
            now = datetime.now()

            if Utils.IsTodayHoliday() == True:
                i=1
                logger.info("Trade Kernel Sleeping Due to holiday")
                pause.until(datetime(now.year,now.month,now.day, 23, 58))
                sleep(1800)
                logger.info("Holiday Finished")
                continue
            else:    
                i=0
                if datetime.now() < datetime(now.year,now.month,now.day, 8, 15):
                    logger.info("Will login to Market @ 8:15am")
                    pause.until(datetime(now.year,now.month,now.day, 8, 15))
                    logger.info("Logged in Market")

                Utils.update_script_master()
                
                threads = []
                client_details = json.loads(open('user_data.json', 'r').read().rstrip())
                read_counter = Value('i', 0)
                total_clients = len(client_details)
                manager = Manager()
                read_threads = manager.list()

                for client in client_details:    
                    t = threading.Thread(target=func, args=(client['name'], client['user_id'], client['password'], client['api_key'], client['secret_key'], read_counter, total_clients, read_threads))
                    t.start()
                    threads.append(t)
                    sleep(3)
                for t in threads:
                    t.join()

                Utils.delete_closed_trades()
                logger.info("Market clossing bell")
                logger.info("algo now in sleep mode")
                pause.until(datetime(now.year,now.month,now.day, 23, 58))
                sleep(900)                       
except:
    logger.info("angel exe failed")
    logger.debug("\n" + "angel exe failed @ " + datetime.now().strftime("%H:%M:%S") + traceback.print_exc())