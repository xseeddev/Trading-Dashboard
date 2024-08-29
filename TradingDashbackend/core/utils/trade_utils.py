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

def get_ltp(angel, token, symbol, max_retries=6, retry_delay=2):
    attempt = 0
    while attempt < max_retries:
        try:
            ltp_data = angel.ltpData("NFO", symbol, token)
            ltp = ltp_data['data']['ltp']
            return ltp
        except Exception as e:
            logger.debug(f"Attempt {attempt + 1} failed: {e}")
            traceback.logger.debug_exc()
            attempt += 1
            time.sleep(retry_delay)
    
    logger.debug("Max retries reached. LTP update failed.")
    return None

def update_nifty_ltp(angel, max_retries=2):
    attempt = 0

    while attempt < max_retries:
        try:
            # Fetch the LTP data for Nifty 50
            nf_cmp = angel.ltpData("NSE", "Nifty 50", "99926000")['data']['ltp']
            return nf_cmp
        except Exception as e:
            # Log the error and increment the attempt counter
            logger.debug(f"Attempt {attempt + 1} failed: {e}")
            traceback.logger.debug_exc()
            attempt += 1
    
    # After max retries, log failure and return -1
    logger.debug("Max retries reached. Nifty LTP update failed.")
    return -1

def fetch_api_trades():
        try:
            url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            scripts = requests.get(url).json()
            scripts_df = pd.DataFrame.from_dict(scripts)
            scripts_df = scripts_df.astype({'strike': float})
            scripts_df.to_csv(r'script_master.csv', index=False)
            logger.info("ScriptMaster updated successfully")
        except Exception as e:
            logger.info("ScriptMaster updation unsuccessfull")


# <------------------------- Trade related functions -------------------------------------->

def available_margin(angel):
    try:
        margin = angel.rmsLimit()['data']
        # Extracting and converting margin values to integers
        net_margin = int(float(margin.get('net', 0)))
        return net_margin
    except KeyError as e:
        raise ValueError(f"Key error: {e} - Check the structure of the API response.")
    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching the available margin: {e}")

def req_margin(angel, buy_leg_token, sell_leg_token):
    data = {
        "positions": [
            {
                "exchange": "NFO",
                "qty": 25,
                "price": 0,
                "productType": "CARRYFORWARD",
                "token": buy_leg_token,
                "tradeType": "BUY"
            },
            {
                "exchange": "NFO",
                "qty": 25,
                "price": 0,
                "productType": "CARRYFORWARD",
                "token": sell_leg_token,
                "tradeType": "SELL"
            }
        ]
    }

    try:
        response = angel.getMarginApi(data)
        margin_req = float(response['data'].get('totalMarginRequired', 0))
        new_margin_req = int(margin_req * 1.20)  # Adding a 20% buffer
        return new_margin_req
    except KeyError as e:
        raise ValueError(f"Key error: {e} - Check the structure of the API response.")
    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching the required margin: {e}")

def trade_req(angel, client, buy_leg_strike, sell_leg_strike, option_type, expiry):
    try:
        script_list = pd.read_csv(r'script_master.csv', low_memory=False)
        
        buy_leg_token, buy_leg_sym = get_token_info(
            df=script_list, strike_price=buy_leg_strike, option_type=option_type, expiry_pref=expiry)
        sell_leg_token, sell_leg_sym = get_token_info(
            df=script_list, strike_price=sell_leg_strike, option_type=option_type, expiry_pref=expiry)

        avail_margin = available_margin(angel)
        margin_per_lot = req_margin(angel, buy_leg_token, sell_leg_token)

        lots = max(int(avail_margin / margin_per_lot), 0)
        qty = lots * 25
        
        return buy_leg_token, buy_leg_sym, sell_leg_token, sell_leg_sym, qty

    except Exception as e:
        write_log(f"{client}: trade_req failed due to {e}")
        traceback.logger.debug_exc()
        return None, None, None, None, 0
    
def update_trade_dataframe(client=None, symbol=None, token=None, buy_date=None, buy_price=None, qty=None, sell_price=None, sell_date=None, leg_status=None, leg_pnl=None):
    try:
        columns = ['client', 'symbol', 'token', 'buy_date', 'buy_price',
                   'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl']
        new_row = pd.Series([client, symbol, token, buy_date, buy_price,
                            qty, sell_price, sell_date, leg_status, leg_pnl], index=columns)
        
        df = pd.read_csv('trades.csv')
        df = df.append(new_row, ignore_index=True)
        df.to_csv('trades.csv', index=False)

    except Exception as e:
        # Log error if something goes wrong
        logger.debug(f"trade_csv updation failed at {datetime.now().strftime('%H:%M:%S')}: {e}")
        traceback.logger.debug_exc()
    
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
        write_log("delete_closed_trades execution failed: " + str(e))
        logger.debug("delete_closed_trades execution failed:")
        traceback.logger.debug_exc()


# <------------------------- Position functions -------------------------------------->

def update_holding(angel):
    try:
        holding = angel.holding()
        if not holding['data']:
            logger.debug("No holdings found.")
            return
        
        holding_df = pd.DataFrame(holding['data'])
        columns_to_keep = ['tradingsymbol', 'quantity', 'averageprice', 'profitandloss', 'pnlpercentage']
        holding_df = holding_df[columns_to_keep]
        
        message = "Holdings:\n"
        for _, row in holding_df.iterrows():
            message += f"Symbol: {row['tradingsymbol']}\n"
            message += f"Quantity: {row['quantity']}\n"
            message += f"Avg Price: {row['averageprice']}\n"
            message += f"P&L: {row['profitandloss']}\n"
            message += f"P&L %: {row['pnlpercentage']}\n\n"
        logger.debug(message)
    
    except Exception as e:
        logger.debug(f"Failed to update holdings: {e}")
        traceback.logger.debug_exc()

def update_positions(angel):
    try:
        time.sleep(2)
        position = angel.position()
        if not position['data']:
            logger.debug("No positions found.")
            return
        
        position_df = pd.DataFrame(position['data'])
        columns_to_keep = ['tradingsymbol', 'netqty', 'totalbuyavgprice', 'totalsellavgprice', 'pnl']
        position_df = position_df[columns_to_keep]
        
        message = "Positions:\n"
        for _, row in position_df.iterrows():
            message += f"Symbol: {row['tradingsymbol']}\n"
            message += f"Quantity: {row['netqty']}\n"
            message += f"Buy Price: {row['totalbuyavgprice']}\n"
            message += f"Sell Price: {row['totalsellavgprice']}\n"
            message += f"P&L: {row['pnl']}\n\n"
        logger.debug(message)
    
    except Exception as e:
        logger.debug(f"Failed to update positions: {e}")
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
		scripts_df = pd.DataFrame.from_dict(scripts)
		scripts_df = scripts_df.astype({'strike': float})
		scripts_df.to_csv(r'script_master.csv', index=False)
		logger.info("ScriptMaster updated successfully")
	except:
		logger.info("ScriptMaster updation unsuccessfull")
		
# <------------------------- Refactor Done -------------------------------------->


def getMarketStartTime(dateTimeObj = None):
	return Utils.getTimeOfDay(9, 15, 0, dateTimeObj)

def getMarketEndTime(dateTimeObj = None):
	return Utils.getTimeOfDay(15, 30, 0, dateTimeObj)


def getTimeOfDay(hours, minutes, seconds, dateTimeObj = None):
	if dateTimeObj == None:
		dateTimeObj = datetime.now()
	dateTimeObj = dateTimeObj.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
	return dateTimeObj





def isMarketOpen():
	if Utils.isTodayHoliday():
		return False
	now = datetime.now()
	marketStartTime = Utils.getMarketStartTime()
	marketEndTime = Utils.getMarketEndTime()
	return now >= marketStartTime and now <= marketEndTime


def isMarketClosedForTheDay():
	# This method returns true if the current time is > marketEndTime
	# Please note this will not return true if current time is < marketStartTime on a trading day
	if isTodayHoliday():
		return True
	now = datetime.now()
	marketEndTime = Utils.getMarketEndTime()
	return now > marketEndTime





def getMonthlyExpiryDayDate(datetimeObj = None):
	if datetimeObj == None:
		datetimeObj = datetime.now()
	year = datetimeObj.year
	month = datetimeObj.month
	lastDay = calendar.monthrange(year, month)[1] # 2nd entry is the last day of the month
	datetimeExpiryDay = datetime(year, month, lastDay)
	while calendar.day_name[datetimeExpiryDay.weekday()] != 'Thursday':
		datetimeExpiryDay = datetimeExpiryDay - timedelta(days=1)
	while Utils.isHoliday(datetimeExpiryDay) == True:
		datetimeExpiryDay = datetimeExpiryDay - timedelta(days=1)

	datetimeExpiryDay = Utils.getTimeOfDay(0, 0, 0, datetimeExpiryDay)
	return datetimeExpiryDay


def isTodayWeeklyExpiryDay():
	todayMarketStartTime = Utils.getMarketStartTime()
	expiryDateTime = Utils.getWeeklyExpiryDayDate()
	expiryDayMarketEndTime = Utils.getMarketEndTime(expiryDateTime)
	if todayMarketStartTime > expiryDayMarketEndTime:
		expiryDateTime = expiryDateTime + timedelta(days=6)
		expiryDateTime = Utils.getWeeklyExpiryDayDate(expiryDateTime)
	todayDate = Utils.getTimeOfToDay(0, 0, 0)
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
	while Utils.isHoliday(datetimeExpiryDay) == True:
		datetimeExpiryDay = datetimeExpiryDay - timedelta(days=1)

	datetimeExpiryDay = Utils.getTimeOfDay(0, 0, 0, datetimeExpiryDay)
	return datetimeExpiryDay


def getExpiry(numWeeksPlus = 0):
	expiryDateTime = Utils.getWeeklyExpiryDayDate()
	todayMarketStartTime = Utils.getMarketStartTime()
	expiryDayMarketEndTime = Utils.getMarketEndTime(expiryDateTime)
	if numWeeksPlus > 0:
		expiryDateTime = expiryDateTime + timedelta(days=numWeeksPlus * 7)
		expiryDateTime = Utils.getWeeklyExpiryDayDate(expiryDateTime)
	if todayMarketStartTime > expiryDayMarketEndTime:
		expiryDateTime = expiryDateTime + timedelta(days=6)
		expiryDateTime = Utils.getWeeklyExpiryDayDate(expiryDateTime)

	year = expiryDateTime.year
	month = expiryDateTime.month
	day = expiryDateTime.day

	#formatted_date = f"date({year}, {month}, {day})"
	formatted_date = expiryDateTime.strftime('%d%b%Y').upper()
	return formatted_date


def getTokenInfo(df, strike_price, option_type, expiry_pref, exch_seg='NFO', instrument_type='OPTIDX', symbol='NIFTY'):
	expiry_day = Utils.getExpiry(expiry_pref)
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


def available_margin(angel):
	margin = angel.rmsLimit()
	margin = margin['data']
	net_margin = int(float(margin['net']))
	availablecash = int(float(margin['availablecash']))
	availableintradaypayin = int(float(margin['availableintradaypayin']))
	availablelimitmargin = int(float(margin['availablelimitmargin']))
	collateral = int(float(margin['collateral']))
	m2munrealized = int(float(margin['m2munrealized']))
	m2mrealized = int(float(margin['m2mrealized']))
	utiliseddebits = int(float(margin['utiliseddebits']))
	utilisedpayout = int(float(margin['utilisedpayout']))
	return net_margin


def req_margin(angel, buy_leg_token, sell_leg_token):

	# Sample request data
	data = {
		"positions": [
			{
				"exchange": "NFO",
				"qty": 25,
				"price": 0,
				"productType": "CARRYFORWARD",
				"token": buy_leg_token,
				"tradeType": "BUY"
			},
			{
				"exchange": "NFO",
				"qty": 25,
				"price": 0,
				"productType": "CARRYFORWARD",
				"token": sell_leg_token,
				"tradeType": "SELL"
			}
		]
	}
	response = angel.getMarginApi(data)
	margin_req = int(response['data']['totalMarginRequired'])
	new_margin_req = int(margin_req+(margin_req * 0.20))
	return new_margin_req


def trade_req(angel, client, buy_leg_strike, sell_leg_strike, option_type, expiry):
	try:
		with file_lock:
			script_list = pd.read_csv(r'script_master.csv', low_memory=False)
		buy_leg_token, buy_leg_sym = Utils.getTokenInfo(df=script_list, strike_price=buy_leg_strike, option_type=option_type, expiry_pref=expiry)
		sell_leg_token, sell_leg_sym = Utils.getTokenInfo(df=script_list, strike_price=sell_leg_strike, option_type=option_type, expiry_pref=expiry)

		avail_margin = Utils.available_margin(angel)
		marigin_per_lot = Utils.req_margin(angel, buy_leg_token, sell_leg_token)
		lots = int(avail_margin/marigin_per_lot)
		qty = int(lots*25)
		return buy_leg_token, buy_leg_sym, sell_leg_token, sell_leg_sym, qty
	except:
		Utils.write_log(client + ": trade_req failed")
		traceback.print_exc()


def update_nf_ltp(angel, i=[0]):
	try:
		nf_cmp = angel.ltpData("NSE", "Nifty 50", "99926000")['data']['ltp']
		i[0] = 0  # Reset i to 0
		return nf_cmp
	except:
		i[0] += 1
		if i[0] > 2:
			print("nf_ltp_update failed")
			i[0] = 0  # Reset i to 0
		return -1


def update_holding(angel):
	try:
		holding = angel.holding()
		if not holding['data']:
			print("no holdings")
		else:
			holding_df = pd.DataFrame(holding['data'])
			holding_df = holding_df.drop(['exchange', 'isin', 't1quantity', 'realisedquantity', 'authorisedquantity', 'product', 'collateralquantity',
											'collateraltype', 'haircut', 'symboltoken', 'close', 'ltp'], axis=1)
			message = "Holding:\n"
			for index, row in holding_df.iterrows():
				message += f"symbol: {row['tradingsymbol']}\n"
				message += f"qty: {row['quantity']}\n"
				message += f"avg_price: {row['averageprice']}\n"
				message += f"pnl: {row['profitandloss']}\n"
				message += f"pnl%: {row['pnlpercentage']}\n\n"
	except:
		traceback.print_exc()


def update_positions(angel):
	try:
		sleep(2)
		position = angel.position()
		if not position['data']:
			print("no positions")
		else:
			position_df = pd.DataFrame(position['data'])
			position_df = position_df.drop(['symboltoken', 'symbolname', 'instrumenttype', 'priceden', 'pricenum', 'genden', 'gennum', 'precision', 'multiplier', 
											'boardlotsize', 'exchange', 'producttype', 'symbolgroup', 'strikeprice', 'optiontype', 'expirydate', 'lotsize', 
											'cfbuyqty', 'cfsellqty', 'cfbuyamount', 'cfsellamount', 'buyavgprice', 'sellavgprice', 'avgnetprice', 'netvalue', 
											'totalbuyvalue', 'totalsellvalue', 'cfbuyavgprice', 'cfsellavgprice', 'netprice', 'buyqty', 'sellqty', 'buyamount', 
											'sellamount', 'realised', 'unrealised', 'ltp', 'close'], axis=1)
			message = "Positions:\n"
			for index, row in position_df.iterrows():
				message += f"symbol: {row['tradingsymbol']}\n"
				message += f"qty: {row['netqty']}\n"
				message += f"buy_price: {row['totalbuyavgprice']}\n"
				message += f"sell_price: {row['totalsellavgprice']}\n"
				message += f"pnl: {row['pnl']}\n\n"
	except:
		traceback.print_exc()


def call_ltp(angel_obj, symbol, token):
	i = 0
	while i < 6:
		try:
			ltp = angel_obj.ltpData("NFO", symbol, token)['data']['ltp']
			return ltp
		except:
			i =+ 1
			sleep(2)
			traceback.print_exc()
			print("option ltp update failed, retrying...")
	print("max retries reached ltp update failed")
	return None





def update_trade_dataframe(client=None, symbol=None, token=None, buy_date=None, buy_price=None, qty=None, sell_price=None, sell_date=None, leg_status=None, leg_pnl=None):
	try:
		columns = ['client', 'symbol', 'token', 'buy_date', 'buy_price', 'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl']
		new_row = pd.Series([client, symbol, token, buy_date, buy_price, qty, sell_price, sell_date, leg_status, leg_pnl], index=columns)
		with file_lock:
			df = pd.read_csv(r'trades.csv')
			df = df._append(new_row, ignore_index=True)
			df.to_csv(r'trades.csv', index=False)
	except:
		Utils.write_log(client + ": trade_csv updation failed")
		print("\n" + "trade_csv updation failed @ " + datetime.now().strftime("%H:%M:%S"))
		traceback.print_exc()



def delete_closed_trades():
	try:
		df = pd.read_csv(r'trades.csv')
		closed_trades = df[(df['leg_status'] == 'CLOSED')]
		if not closed_trades.empty:
			df = df.drop(closed_trades.index)
			df.to_csv(r'trades.csv', index=False)
	except:
		Utils.write_log("delete_closed_trades exe failed")
		print("delete_closed_trades exe failed")
		traceback.print_exc()