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
from TradingDashbackend.core.utils import order_exec
from TradingDashbackend.core.master import SCRIPTS_MASTER_DF
from TradingDashbackend.core.master import TRADES_DF


# <------------------------- Date, day, time checking -------------------------------------->

dateFormat = '%Y-%m-%d'
timeFormat = '%H:%M:%S'
dateTimeFormat = f'{dateFormat} {timeFormat}'
logger = setup_logger("Core:Trade Utils")

def get_holidays_set():
    holidays = pd.read_csv('holidays.csv')
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

# <------------------------- Instrument related functions -------------------------------------->

def get_token_info(df, strike_price, option_type, expiry_pref, exch_seg='NFO', instrument_type='OPTIDX', symbol='NIFTY'):
        expiry_day = expiry_pref.upper()  # Ensure expiry_pref is in the correct format
        
        info = df[
            (df['instrumenttype'] == instrument_type) &
            (df['strike'] == float(strike_price * 100)) &
            (df['expiry'] == expiry_day) &
            (df['exch_seg'] == exch_seg) &
            (df['name'] == symbol) &
            (df['symbol'].str.endswith(option_type))
        ]
        
        if info.empty:
            raise ValueError("No matching records found for the given criteria.")
        
        df_info = info.iloc[0]
        option_token = df_info['token']
        option_sym = df_info['symbol']
        
        return option_token, option_sym


# <------------------------- Trade related functions -------------------------------------->

 
def delete_closed_trades(file_path='trades.csv'):
    try:        
        trades = pd.read_csv(file_path)
        closed_trades = trades[trades['leg_status'] == 'CLOSED']
        
        if not closed_trades.empty:
            trades = trades.drop(closed_trades.index)
            
            trades.to_csv(file_path, index=False)
            logger.debug("Closed trades deleted successfully.")
        else:
            logger.debug("No closed trades to delete.")

    except Exception as e:
        logger.info("delete_closed_trades execution failed: " + str(e))
        logger.debug("delete_closed_trades execution failed:")
        traceback.logger.debug_exc()



# <------------------------- Math Util functions -------------------------------------->

def roundOff(price): # Round off to 2 decimal places
	return round(price, 2)

def roundToNSEPrice(price):
	x = round(price, 2) * 20
	y = math.ceil(x)
	return y / 20

def getHolidayList():
	with open(r'holidays.json', 'r') as holidays:
		holidaysData = json.load(holidays)
		return holidaysData
	
def isTodayHoliday():
	datetimeObj = datetime.now()
	dayOfWeek = calendar.day_name[datetimeObj.weekday()]
	if dayOfWeek == 'Saturday' or dayOfWeek == 'Sunday':
		return True

	dateStr = datetimeObj.strftime(dateFormat)
	holidays = getHolidayList()
	if (dateStr in holidays):
		return True
	else:
		return False

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

def getMarketStartTime(dateTimeObj = None):
    if dateTimeObj == None:
        dateTimeObj = datetime.now()
    dateTimeObj = dateTimeObj.replace(hour=9, minute=15, second=0, microsecond=0)
    return dateTimeObj

def getMarketEndTime(dateTimeObj = None):
    if dateTimeObj == None:
        dateTimeObj = datetime.now()
    dateTimeObj = dateTimeObj.replace(hour=15, minute=30, second=0, microsecond=0)
    return dateTimeObj
		
def isMarketOpen():
	if isTodayHoliday():
		return False
	now = datetime.now()
	marketStartTime = getMarketStartTime()
	marketEndTime = getMarketEndTime()
	return now >= marketStartTime and now <= marketEndTime

def isMarketClosedForTheDay():
	# This method returns true if the current time is > marketEndTime
	# Please note this will not return true if current time is < marketStartTime on a trading day
	if isTodayHoliday():
		return True
	now = datetime.now()
	marketEndTime = getMarketEndTime()
	return now > marketEndTime

def getMonthlyExpiryDayDate(dateTimeObj = None):
    if dateTimeObj == None:
        dateTimeObj = datetime.now()
    year = dateTimeObj.year
    month = dateTimeObj.month
    lastDay = calendar.monthrange(year, month)[1] # 2nd entry is the last day of the month
    dateTimeExpiryDay = datetime(year, month, lastDay)
    while calendar.day_name[dateTimeExpiryDay.weekday()] != 'Thursday':
        dateTimeExpiryDay = dateTimeExpiryDay - timedelta(days=1)
    while isTodayHoliday(dateTimeExpiryDay) == True:
        dateTimeExpiryDay = dateTimeExpiryDay - timedelta(days=1)
        
    if dateTimeExpiryDay == None:
        dateTimeExpiryDay = datetime.now()
        dateTimeExpiryDay = dateTimeObj.replace(hour=0, minute=0, second=0, microsecond=0)
    return dateTimeExpiryDay

def getTimeOfDay(hours, minutes, seconds, dateTimeObj = None):
    if dateTimeObj == None:
        dateTimeObj = datetime.now()
    dateTimeObj = dateTimeObj.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
    return dateTimeObj


def isTodayWeeklyExpiryDay():
	todayMarketStartTime = getMarketStartTime()
	expiryDateTime = getWeeklyExpiryDayDate()
	expiryDayMarketEndTime = getMarketEndTime(expiryDateTime)
	if todayMarketStartTime > expiryDayMarketEndTime:
		expiryDateTime = expiryDateTime + timedelta(days=6)
		expiryDateTime = getWeeklyExpiryDayDate(expiryDateTime)
	todayDate = getTimeOfDay(0, 0, 0,datetime.now())
	print("today's date: "+ str(todayDate) + "  weekly expiry: " + str(expiryDateTime))
	if expiryDateTime == todayDate:
		return True
	return False

def getWeeklyExpiryDayDate(dateTimeObj = None):
	if dateTimeObj == None:
		dateTimeObj = datetime.now()
	daysToAdd = 0
	if dateTimeObj.weekday() >= 3:
		daysToAdd = -1 * (dateTimeObj.weekday() - 3)
	else:
		daysToAdd = 3 - dateTimeObj.weekday()
	datetimeExpiryDay = dateTimeObj + timedelta(days=daysToAdd)
	while isTodayHoliday(datetimeExpiryDay) == True:
		datetimeExpiryDay = datetimeExpiryDay - timedelta(days=1)

	datetimeExpiryDay = getTimeOfDay(0, 0, 0, datetimeExpiryDay)
	return datetimeExpiryDay


def getExpiry(numWeeksPlus = 0):
	expiryDateTime = getWeeklyExpiryDayDate()
	todayMarketStartTime = getMarketStartTime()
	expiryDayMarketEndTime = getMarketEndTime(expiryDateTime)
	if numWeeksPlus > 0:
		expiryDateTime = expiryDateTime + timedelta(days=numWeeksPlus * 7)
		expiryDateTime = getWeeklyExpiryDayDate(expiryDateTime)
	if todayMarketStartTime > expiryDayMarketEndTime:
		expiryDateTime = expiryDateTime + timedelta(days=6)
		expiryDateTime = getWeeklyExpiryDayDate(expiryDateTime)

	year = expiryDateTime.year
	month = expiryDateTime.month
	day = expiryDateTime.day

	#formatted_date = f"date({year}, {month}, {day})"
	formatted_date = expiryDateTime.strftime('%d%b%Y').upper()
	return formatted_date

def getTokenInfo(df, strike_price, option_type, expiry_pref, exch_seg='NFO', instrument_type='OPTIDX', symbol='NIFTY'):
	expiry_day = getExpiry(expiry_pref)
	info = df[(df['instrumenttype'] == instrument_type) & 
				(df['strike'] == float(strike_price*100)) &
				(df['expiry'] == expiry_day) &
				(df['exch_seg'] == 'NFO') &
				(df['name'] == symbol) &
				(df['symbol'].str.endswith(option_type))]

	df_info = info.iloc[0]
	option_token = df_info['token']
	option_sym = df_info['symbol']
	return option_token, option_sym


def trade_req(user,buy_leg_strike, sell_leg_strike, option_type, expiry):
    try:
        buy_leg_token, buy_leg_sym = getTokenInfo(df=SCRIPTS_MASTER_DF, strike_price=buy_leg_strike, option_type=option_type, expiry_pref=expiry)
        sell_leg_token, sell_leg_sym = getTokenInfo(df=SCRIPTS_MASTER_DF, strike_price=sell_leg_strike, option_type=option_type, expiry_pref=expiry)


        avail_margin = user.available_margin()
        marigin_per_lot = user.req_margin(buy_leg_token, sell_leg_token)

        lots = int(avail_margin/marigin_per_lot)
        qty = int(lots*25)
        return buy_leg_token, buy_leg_sym, sell_leg_token, sell_leg_sym, qty
    except:
        logger.info(user.Name + ": trade_req failed")
        logger.debug(user.Name + ": trade_req failed" + traceback.print_exc())


def update_trade_dataframe(user ,symbol=None, token=None, buy_date=None, buy_price=None, qty=None, sell_price=None, sell_date=None, leg_status=None, leg_pnl=None):
    try:
        columns = ['client', 'symbol', 'token', 'buy_date', 'buy_price', 'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl']
        new_row = pd.Series([user.Name, symbol, token, buy_date, buy_price, qty, sell_price, sell_date, leg_status, leg_pnl], index=columns)
        df = TRADES_DF._append(new_row, ignore_index=True)
        logger.info(user.Name + ": Updated Trades DF")
    except:
        logger.info(user.Name + ": trade_csv updation failed")
        logger.debug("\n" + "trade_csv updation failed @ " + datetime.now().strftime("%H:%M:%S") + traceback.print_exc())

def delete_closed_trades():
	try:
		df = TRADES_DF
		closed_trades = df[(df['leg_status'] == 'CLOSED')]
		if not closed_trades.empty:
			df = df.drop(closed_trades.index)
			TRADES_DF = df
	except:
		logger.info("delete_closed_trades exe failed")
		logger.debug("delete_closed_trades exe failed" + traceback.print_exc())
          
# <------------------------- Refactor Done -------------------------------------->