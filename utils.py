from datetime import datetime, timedelta
from time import sleep
import pandas as pd
import threading
import traceback
import requests
import calendar
import logging
import math
import uuid
import time
import json

file_lock = threading.Lock()

class Utils:
	dateFormat = "%Y-%m-%d"
	timeFormat = "%H:%M:%S"
	dateTimeFormat = "%Y-%m-%d %H:%M:%S"

	@staticmethod
	def roundOff(price): # Round off to 2 decimal places
		return round(price, 2)
    
	@staticmethod
	def roundToNSEPrice(price):
		x = round(price, 2) * 20
		y = math.ceil(x)
		return y / 20

	@staticmethod
	def getMarketStartTime(dateTimeObj = None):
		return Utils.getTimeOfDay(9, 15, 0, dateTimeObj)

	@staticmethod
	def getMarketEndTime(dateTimeObj = None):
		return Utils.getTimeOfDay(15, 30, 0, dateTimeObj)

	@staticmethod
	def getTimeOfDay(hours, minutes, seconds, dateTimeObj = None):
		if dateTimeObj == None:
		  dateTimeObj = datetime.now()
		dateTimeObj = dateTimeObj.replace(hour=hours, minute=minutes, second=seconds, microsecond=0)
		return dateTimeObj

	@staticmethod
	def getHolidays():
		with open(r'C:\algo\holidays.json', 'r') as holidays:
			holidaysData = json.load(holidays)
			return holidaysData

	@staticmethod
	def isMarketOpen():
		if Utils.isTodayHoliday():
		  return False
		now = datetime.now()
		marketStartTime = Utils.getMarketStartTime()
		marketEndTime = Utils.getMarketEndTime()
		return now >= marketStartTime and now <= marketEndTime

	@staticmethod
	def isMarketClosedForTheDay():
		# This method returns true if the current time is > marketEndTime
		# Please note this will not return true if current time is < marketStartTime on a trading day
		if Utils.isTodayHoliday():
		  return True
		now = datetime.now()
		marketEndTime = Utils.getMarketEndTime()
		return now > marketEndTime

	@staticmethod
	def getTimeOfToDay(hours, minutes, seconds):
		return Utils.getTimeOfDay(hours, minutes, seconds, datetime.now())

	@staticmethod
	def getTodayDateStr():
		return Utils.convertToDateStr(datetime.now())

	@staticmethod
	def convertToDateStr(datetimeObj):
		return datetimeObj.strftime(Utils.dateFormat)

	@staticmethod
	def isHoliday(datetimeObj):
		dayOfWeek = calendar.day_name[datetimeObj.weekday()]
		if dayOfWeek == 'Saturday' or dayOfWeek == 'Sunday':
		  return True

		dateStr = Utils.convertToDateStr(datetimeObj)
		holidays = Utils.getHolidays()
		if (dateStr in holidays):
		  return True
		else:
		  return False

	@staticmethod
	def isTodayHoliday():
		return Utils.isHoliday(datetime.now())

	@staticmethod
	def IsTodayHoliday():
		today = datetime.today()
		dateStr = Utils.convertToDateStr(today)
		if today.weekday() in [5, 6]: # Weekend
			print("Market is closed because of weekend")
			print("Market is closed because of weekend")
			return True
		elif dateStr in Utils.getHolidays(): # National Holiday
			print("Market is closed because of national holiday")
			print("Market is closed because of national holiday")
			return True
		return False

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
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

	@staticmethod
	def call_ltp(angel, symbol, token):
		i = 0
		while i < 6:
			try:
				ltp = angel.ltpData("NFO", symbol, token)['data']['ltp']
				return ltp
			except:
				i =+ 1
				sleep(2)
				traceback.print_exc()
				print("option ltp update failed, retrying...")
		print("max retries reached ltp update failed")
		return None

	@staticmethod
	def update_script_master():
		try:
			url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
			scripts = requests.get(url).json()
			scripts_df = pd.DataFrame.from_dict(scripts)
			scripts_df = scripts_df.astype({'strike': float})
			scripts_df.to_csv(r'script_master.csv', index=False)
			Utils.write_log("ScriptMaster updated successfully")
		except:
		    Utils.write_log("ScriptMaster updation unsuccessfull")

	@staticmethod
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

	@staticmethod
	def write_log(message):
		current_date = datetime.now().strftime("%Y-%d-%m")
		current_time = datetime.now().strftime("%H:%M:%S")
		log_entry = {"time": current_time, "message": message}
		try:
			with open("activity_log.json", "r+") as f:
				try:
					data = json.load(f)
				except json.JSONDecodeError:
					data = {}
				
				data.setdefault(current_date, []).append(log_entry)
				
				f.seek(0)
				json.dump(data, f, indent=4)
				f.truncate()
		except FileNotFoundError:
			with open("activity_log.json", "w") as f:
				json.dump({current_date: [log_entry]}, f, indent=4)


	@staticmethod
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