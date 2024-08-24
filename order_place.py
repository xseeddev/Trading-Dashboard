from datetime import datetime, date
from utils import Utils
from time import sleep
import pandas as pd
import traceback
import order
import json

def buy_order(angel, client, buy_qty, buy_token, buy_symbol):
    try:
        buy_ltp = Utils.call_ltp(angel, buy_symbol, buy_token)
        buy_Orderid = order.place_order_buy(angel, buy_symbol, buy_token, buy_qty, buy_ltp+0.5)
        i=0
        while True:
            try:
                sleep(1)
                orderbook = angel.orderBook()
                buy_rec = orderbook['data']
                for buy_row in buy_rec:
                    if i < 3:
                        if (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'open'):
                            try:
                                buy_ltp = angel.ltpData("NFO", buy_symbol, buy_token)['data']['ltp']
                                m_qty = int(buy_row['unfilledshares'])
                                buy_modify_Orderid = order.modify_order(angel, buy_Orderid, buy_ltp+0.5, buy_symbol, buy_token, m_qty)
                                i=i+1
                                Utils.write_log(client + ": buy_order modified as price skipped")
                            except:
                                i=i+1
                                traceback.print_exc()
                                Utils.write_log(client + ": buy_modify_order failed")

                        elif (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'complete'):
                            try:
                                buy_symbol = buy_row['tradingsymbol']
                                buy_qty = int(buy_row['quantity'])
                                buy_price = buy_row['averageprice']
                                buy_date = buy_row['updatetime']
                                Utils.write_log(client + ": buy_leg_order placed successfully")
                                return buy_symbol, buy_qty, buy_price, buy_date
                            except:
                                Utils.write_log(client + ": buy_order executed, but orderbook calling failed")
                                print("buy_order executed, but orderbook calling failed")
                                traceback.print_exc()
                                return -1, -1, -1, -1

                        elif (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'rejected'):
                            Utils.write_log(client + ": buy_order_placement_rejected")
                            return -1, -1, -1, -1

                        elif (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'cancelled'):
                            Utils.write_log(client + ": buy_order_placement_cancelled")
                            return -1, -1, -1, -1

                    else:
                        Utils.write_log(client + ": buy_order_placement_failed")
                        return -1, -1, -1, -1
            except:
                Utils.write_log(client + ": orderbook calling for buy leg failed, retrying...")
                print("orderbook calling 4r buy leg failed, retrying...") 
                traceback.print_exc()
    except:
        Utils.write_log(client + ": buy_order exe failed")
        print("buy_order exe failed")
        traceback.print_exc()

def sell_order(angel, client, sell_qty, sell_token, sell_symbol):
    try:
        sell_ltp = Utils.call_ltp(angel, sell_symbol, sell_token)
        if sell_ltp >= 1: sell_ltp = sell_ltp-0.5
        sell_Orderid = order.place_order_sell(angel, sell_symbol, sell_token, sell_qty, sell_ltp)
        i=0
        while True:
            try:
                sleep(1)
                orderbook = angel.orderBook()
                sell_rec = orderbook['data']
                for sell_row in sell_rec:
                    if i < 3:
                        if (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'open'):
                            try:
                                sell_ltp = angel.ltpData("NFO", sell_symbol, sell_token)['data']['ltp']
                                if sell_ltp >= 1: sell_ltp = sell_ltp-0.5
                                m_qty = int(sell_row['unfilledshares'])
                                sell_modify_Orderid = order.modify_order(angel, sell_Orderid, sell_ltp, sell_symbol, sell_token, m_qty)
                                i=i+1
                                Utils.write_log(client + ": sell_order modified as price skipped")
                            except:
                                i=i+1
                                traceback.print_exc()
                                Utils.write_log(client + ": sell_modify_order failed")

                        elif (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'complete'):
                            try:
                                sell_symbol = sell_row['tradingsymbol']
                                sell_qty = int(sell_row['quantity'])
                                sell_price = sell_row['averageprice']
                                sell_date = sell_row['updatetime']
                                Utils.write_log(client + ": sell_leg_order placed successfully")
                                return sell_symbol, sell_qty, sell_price, sell_date
                            except:
                                Utils.write_log(client + ": sell_order executed, but orderbook calling failed")
                                print("sell_order executed, but orderbook calling failed")
                                traceback.print_exc()
                                return -1, -1, -1, -1

                        elif (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'rejected'):
                            Utils.write_log(client + ": sell_order_placement_rejected")
                            return -1, -1, -1, -1

                        elif (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'cancelled'):
                            Utils.write_log(client + ": sell_order_placement_cancelled")
                            return -1, -1, -1, -1
                    else:
                        Utils.write_log(client + ": sell_order_placement_failed")
                        print("sell_order_placement_failed")
                        return -1, -1, -1, -1
            except:
                Utils.write_log(client + ": orderbook calling 4r sell leg failed, retrying...")
                print("orderbook calling 4r sell leg failed, retrying...")  
                traceback.print_exc() 
    except:
        Utils.write_log(client + ": sell_order exe failed")
        print("sell_order exe failed")
        traceback.print_exc()

def order_exe(angel, client, buy_strike, sell_strike, option_type, expiry):
    try:
        buy_token, buy_symbol, sell_token, sell_symbol, qty = Utils.trade_req(angel, client, buy_strike, sell_strike, option_type, expiry)
        if qty>200:
            buy_sym, buy_qty, buy_price, buy_date = buy_order(angel, client, qty, buy_token, buy_symbol)
            if buy_sym==buy_symbol and buy_qty==qty:
                sell_sym, sell_qty, sell_price, sell_date = sell_order(angel, client, qty, sell_token, sell_symbol)
                if sell_sym==sell_symbol and abs(sell_qty)==qty:
                    Utils.update_trade_dataframe(client=client, symbol=sell_symbol, qty=-(sell_qty), sell_price=sell_price, token=sell_token, sell_date=sell_date)
                    Utils.update_trade_dataframe(client=client, symbol=buy_symbol, qty=buy_qty, buy_price=buy_price, token=buy_token, buy_date=buy_date)
                    Utils.write_log(client + ": complete order exe successfull")
        else:
            Utils.write_log(client + ": min. margin req. not fullfilled")
    except:
        Utils.write_log(client + ": order exe failed")
        print("order exe failed")
        traceback.print_exc()