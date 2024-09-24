'''
1. Date, day, time checking
2. Instrument related functions
3. Trade related functions
4. Position functions
5. Logging functions
'''

import time
import json
import requests
import traceback
import pandas as pd
from datetime import datetime, time, timedelta
from time import sleep
import threading
import calendar
import math
from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.master import SCRIPTS_MASTER_DF
from TradingDashbackend.core.master import TRADES_DF
from TradingDashbackend.core.utils import trade_user


# <------------------------- Date, day, time checking -------------------------------------->

dateFormat = '%Y-%m-%d'
timeFormat = '%H:%M:%S'
dateTimeFormat = f'{dateFormat} {timeFormat}'
logger = setup_logger("Core:Trade Utils")

def get_holidays_set():
    holidays = pd.read_csv('TradingDashbackend/core/utils/holidays.json')
    holidays['holiday_date'] = pd.to_datetime(holidays['holiday_date']).dt.date
    holidays_set = set(holidays['holiday_date'])
    return holidays_set


def is_market_open(market_open_time='09:15', market_close_time='15:30'):
    now = datetime.now()
    current_date = now.date()
    current_time = now.time()
    market_open = time.fromisoformat(market_open_time)
    market_close = time.fromisoformat(market_close_time)

    if now.weekday() in [5, 6]:
        logger.debug(f"Today ({current_date}) is a weekend. Market is closed.")
        return False

    if current_date in get_holidays_set():
        logger.debug(f"Today ({current_date}) is a holiday. Market is closed.")
        return False

    if market_open <= current_time <= market_close:
        logger.debug(f"Market is open. Current time is {now.strftime('%H:%M:%S')}.")
        return True
    else:
        logger.debug(f"Market is closed. Current time is {now.strftime('%H:%M:%S')}.")
        return False

# <------------------------- Expiration functions -------------------------------------->

def get_monthly_expiry_day(date_obj=None, holidays=None):
    if date_obj is None:
        date_obj = datetime.now()
    
    if holidays is None:
        holidays = get_holidays_set()

    year = date_obj.year
    month = date_obj.month

    try:
        last_day = (datetime(year, month + 1, 1) - timedelta(days=1)).day
        expiry_date = datetime(year, month, last_day)
        
        weekday = expiry_date.weekday()
        days_to_subtract = (weekday - 3 + 7) % 7  # 3 corresponds to Thursday (0=Monday, 6=Sunday)
        expiry_date -= timedelta(days=days_to_subtract)
        
        while expiry_date in holidays:
            expiry_date -= timedelta(days=7)  # Move back to the previous week
        expiry_date = expiry_date.replace(hour=0, minute=0, second=0, microsecond=0)

        return expiry_date

    except Exception as e:
        logger.debug(f"Error calculating the monthly expiry day: {str(e)}")
        return None
    
def get_market_start_time(date_obj=None):
    if date_obj is None:
        date_obj = datetime.now()
    
    return date_obj.replace(hour=9, minute=0, second=0, microsecond=0)

def get_market_end_time(date_obj=None):
    if date_obj is None:
        date_obj = datetime.now()
    
    return date_obj.replace(hour=15, minute=30, second=0, microsecond=0)

def get_weekly_expiry_day(date_obj=None):
    if date_obj is None:
        date_obj = datetime.now()

    weekday = date_obj.weekday()
    days_to_thursday = (3 - weekday + 7) % 7  # 3 corresponds to Thursday
    next_thursday = date_obj + timedelta(days=days_to_thursday)
    
    return next_thursday.replace(hour=0, minute=0, second=0, microsecond=0)
    
def is_today_weekly_expiry_day():
    today_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_market_start_time = get_market_start_time()
    expiry_date_time = get_weekly_expiry_day()
    expiry_day_market_end_time = get_market_end_time(expiry_date_time)
    
    if today_market_start_time > expiry_day_market_end_time:
        expiry_date_time += timedelta(days=7)
        expiry_date_time = get_weekly_expiry_day(expiry_date_time)

    logger.debug(f"Today's date: {today_date}, Weekly expiry: {expiry_date_time}")
    
    return expiry_date_time == today_date

def get_expiry(num_weeks_plus=0):
        expiry_date = get_weekly_expiry_day()
        if num_weeks_plus > 0:
            expiry_date += timedelta(weeks=num_weeks_plus)
            expiry_date = get_weekly_expiry_day(expiry_date)
        
        today_market_start_time = get_market_start_time()
        expiry_day_market_end_time = get_market_end_time(expiry_date)
        
        if today_market_start_time > expiry_day_market_end_time:
            expiry_date += timedelta(weeks=1)
            expiry_date = get_weekly_expiry_day(expiry_date)
        
        return expiry_date.strftime('%d%b%Y').upper()

# <------------------------- Trade related functions -------------------------------------->

def delete_closed_trades():
    try:        
        closed_trades = TRADES_DF[TRADES_DF['leg_status'] == 'CLOSED']
        
        if not closed_trades.empty:
            TRADES_DF = TRADES_DF.drop(closed_trades.index)

            logger.debug("Closed trades deleted successfully.")
            logger.info("Deleted Closed Trades")
        else:
            logger.debug("No closed trades to delete.")

    except Exception as e:
        logger.info("delete_closed_trades execution failed: " + str(e))
        logger.debug("delete_closed_trades execution failed:")
        traceback.logger.debug_exc()

def update_script_master():
    try:
        url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
        scripts = requests.get(url).json()
        SCRIPTS_MASTER_DF = pd.DataFrame.from_dict(scripts)
        SCRIPTS_MASTER_DF = SCRIPTS_MASTER_DF.astype({'strike': float})
        # scripts_df.to_csv(r'script_master.csv', index=False)
        logger.info("ScriptMaster updated successfully")
    except:
        logger.info("ScriptMaster updation unsuccessfull")

def trade_req(user,buy_leg_strike, sell_leg_strike, option_type, expiry):
    try:
        buy_leg_token, buy_leg_sym = getTokenInfo(df=SCRIPTS_MASTER_DF, strike_price=buy_leg_strike, option_type=option_type, expiry_pref=expiry)
        sell_leg_token, sell_leg_sym = getTokenInfo(df=SCRIPTS_MASTER_DF, strike_price=sell_leg_strike, option_type=option_type, expiry_pref=expiry)
        avail_margin = user.available_margin()
        marigin_per_lot = user.req_margin(buy_leg_token, sell_leg_token)

        lots = int(avail_margin/marigin_per_lot)
        qty = int(lots*25)
        logger.info(user.Name + ": trade_req Success")
        return buy_leg_token, buy_leg_sym, sell_leg_token, sell_leg_sym, qty
    except:
        logger.info(user.Name + ": trade_req failed")
        logger.debug(user.Name + ": trade_req failed" + traceback.print_exc())

def getTokenInfo(df, strike_price, option_type, expiry_pref, exch_seg='NFO', instrument_type='OPTIDX', symbol='NIFTY'):
    # Ensure expiry_pref is in the correct format
    # expiry_day = expiry_pref.upper() 
    # expiry_day = get_expiry(expiry_pref)


	info = df[(df['instrumenttype'] == instrument_type) & 
				(df['strike'] == float(strike_price*100)) &
				(df['expiry'] == get_expiry(expiry_pref)) &
				(df['exch_seg'] == exch_seg) &
				(df['name'] == symbol) &
				(df['symbol'].str.endswith(option_type))]

	df_info = info.iloc[0]
	option_token = df_info['token']
	option_sym = df_info['symbol']
	return option_token, option_sym

# <------------------------- Math Util functions -------------------------------------->

def roundOff(price): # Round off to 2 decimal places
	return round(price, 2)

def roundToNSEPrice(price):
	x = round(price, 2) * 20
	y = math.ceil(x)
	return y / 20
def adjust_ltp(order_type: str, ltp: float) -> float:
    if order_type == 'buy':
        return ltp + 0.5
    elif order_type == 'sell' and ltp >= 1:
        return ltp - 0.5
    return ltp

# <------------------------- Trade Helpers functions -------------------------------------->

def update_trade_dataframe(
    angel: trade_user,
    symbol: str,
    token: str,
    buy_date: str,
    buy_price: float,
    qty: int,
    sell_price: float,
    sell_date: str,
    leg_status: str,
    leg_pnl: float
) -> None:
    """
    Updates the trade dataframe by appending a new trade entry.

    Args:
    - client (str): The client identifier.
    - symbol (str): The trading symbol.
    - token (str): The token associated with the trade.
    - buy_date (str): The date the asset was bought.
    - buy_price (float): The price at which the asset was bought.
    - qty (int): The quantity of the asset traded.
    - sell_price (float): The price at which the asset was sold.
    - sell_date (str): The date the asset was sold.
    - leg_status (str): The status of the trade leg.
    - leg_pnl (float): The profit and loss for the trade leg.

    Returns:
    - None
    """
    try:
        client = angel.Name
        columns = ['client', 'symbol', 'token', 'buy_date', 'buy_price', 'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl']
        new_row = pd.Series([client, symbol, token, buy_date, buy_price, qty, sell_price, sell_date, leg_status, leg_pnl], index=columns)

        df = SCRIPTS_MASTER_DF
        df = df.append(new_row, ignore_index=True)
        # df.to_csv('trades.csv', index=False)

        logger.info("Trade data updated successfully for client: %s", client)

    except Exception as e:
        logger.info("Failed to update trade CSV for client %s: %s", client, str(e))
        logger.debug(f"\nTrade CSV update failed @ {datetime.now().strftime('%H:%M:%S')}")


def update_trade_status(dataframe, index, result):
    """Update the trade status in the DataFrame based on the result."""
    try:
        quantity = result[1]
        price = result[2]
        date = result[3]
        order_type = result[4]

        if order_type == 'buy':
            dataframe.at[index, 'buy_price'] = price
            dataframe.at[index, 'buy_date'] = date
            dataframe.at[index, 'quantity'] = abs(quantity)
            dataframe.at[index, 'trade_status'] = 'CLOSED'
            dataframe.at[index, 'trade_pnl'] = (dataframe.at[index, 'sell_price'] - price) * abs(quantity)

        elif order_type == 'sell':
            dataframe.at[index, 'sell_price'] = price
            dataframe.at[index, 'sell_date'] = date
            dataframe.at[index, 'quantity'] = abs(quantity)
            dataframe.at[index, 'trade_status'] = 'CLOSED'
            dataframe.at[index, 'trade_pnl'] = (price - dataframe.at[index, 'buy_price']) * abs(quantity)

        return dataframe

    except Exception as e:
        logger.info(f"Error updating trade status: {str(e)}")
        logger.debug(f"Error updating trade status: {str(e)}")
        # traceback.print_exc()
        return dataframe