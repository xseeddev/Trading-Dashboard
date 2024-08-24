from datetime import datetime, date
from utils import Utils
from time import sleep
import pandas as pd
import order_place
import threading
import traceback

def exit_active_legs(angel, client):
    try:
        file_lock = threading.Lock()
        with file_lock:
            df = pd.read_csv(r'trades.csv')

        active_legs = df[(df['leg_status'] != 'CLOSED') & (df['client'] == client)]
        active_legs = active_legs.sort_values(by='qty')

        for index, row in active_legs.iterrows():

            if row['qty'] < 0 :
                buy_symbol, buy_qty, buy_price, buy_date = order_place.buy_order(angel, abs(row['qty']), row['token'], row['symbol'])
                df.at[index, 'buy_price'] = buy_price
                df.at[index, 'buy_date'] = buy_date
                df.at[index, 'qty'] = abs(buy_qty)
                df.at[index, 'leg_status'] = 'CLOSED'
                df.at[index, 'leg_pnl'] = ((df.at[index, 'sell_price']-buy_price)*df.at[index, 'qty'])

            elif row['qty'] > 0 :
                sell_symbol, sell_qty, sell_price, sell_date = order_place.sell_order(angel, abs(row['qty']), row['token'], row['symbol'])
                df.at[index, 'sell_price'] = sell_price
                df.at[index, 'sell_date'] = sell_date
                df.at[index, 'qty'] = abs(sell_qty)
                df.at[index, 'leg_status'] = 'CLOSED'
                df.at[index, 'leg_pnl'] = (sell_price-df.at[index, 'buy_price'])*df.at[index, 'qty']

        with file_lock:
            df.to_csv(r'trades.csv', index=False)

        with file_lock:
            df = pd.read_csv(r'trades.csv')
            active_legs = df[(df['leg_status'] != 'CLOSED') & (df['client'] == client)]
            if not active_legs.empty:
                Utils.write_log(client + ": trade still open")
            else:
                Utils.write_log(client + ": trade completed successfully")

    except:
        Utils.write_log(client + ": trade exit failed")
        print("\n" + client +": trade_exit exe failed @ " + datetime.now().strftime("%H:%M:%S"))
        traceback.print_exc()