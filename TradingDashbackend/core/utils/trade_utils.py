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

# <------------------------- Date, day, time checking -------------------------------------->

dateFormat = '%Y-%m-%d'
timeFormat = '%H:%M:%S'
dateTimeFormat = f'{dateFormat} {timeFormat}'

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
        print(f"Today ({current_date}) is a weekend. Market is closed.")
        return False

    if current_date in get_holidays_set():
        print(f"Today ({current_date}) is a holiday. Market is closed.")
        return False

    if market_open <= current_time <= market_close:
        print(f"Market is open. Current time is {now.strftime('%H:%M:%S')}.")
        return True
    else:
        print(f"Market is closed. Current time is {now.strftime('%H:%M:%S')}.")
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
        print(f"Error calculating the monthly expiry day: {str(e)}")
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

    print(f"Today's date: {today_date}, Weekly expiry: {expiry_date_time}")
    
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
            print(f"Attempt {attempt + 1} failed: {e}")
            traceback.print_exc()
            attempt += 1
            time.sleep(retry_delay)
    
    print("Max retries reached. LTP update failed.")
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
            print(f"Attempt {attempt + 1} failed: {e}")
            traceback.print_exc()
            attempt += 1
    
    # After max retries, log failure and return -1
    print("Max retries reached. Nifty LTP update failed.")
    return -1

def fetch_api_trades():
        try:
            url = 'https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json'
            scripts = requests.get(url).json()
            scripts_df = pd.DataFrame.from_dict(scripts)
            scripts_df = scripts_df.astype({'strike': float})
            scripts_df.to_csv(r'script_master.csv', index=False)
            write_log("ScriptMaster updated successfully")
        except Exception as e:
            write_log("ScriptMaster updation unsuccessfull")


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
        traceback.print_exc()
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
        print(f"trade_csv updation failed at {datetime.now().strftime('%H:%M:%S')}: {e}")
        traceback.print_exc()
    
def delete_closed_trades(file_path='trades.csv'):
    try:        
        trades = pd.read_csv(file_path)
        closed_trades = trades[trades['leg_status'] == 'CLOSED']
        
        if not closed_trades.empty:
            trades = trades.drop(closed_trades.index)
            
            trades.to_csv(file_path, index=False)
            print("Closed trades deleted successfully.")
        else:
            print("No closed trades to delete.")

    except Exception as e:
        write_log("delete_closed_trades execution failed: " + str(e))
        print("delete_closed_trades execution failed:")
        traceback.print_exc()


# <------------------------- Position functions -------------------------------------->

def update_holding(angel):
    try:
        holding = angel.holding()
        if not holding['data']:
            print("No holdings found.")
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
        print(message)
    
    except Exception as e:
        print(f"Failed to update holdings: {e}")
        traceback.print_exc()

def update_positions(angel):
    try:
        time.sleep(2)
        position = angel.position()
        if not position['data']:
            print("No positions found.")
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
        print(message)
    
    except Exception as e:
        print(f"Failed to update positions: {e}")
        traceback.print_exc()

# <------------------------- Logging functions -------------------------------------->

def write_log(message, log_path=r'C:\algo\backend\activity_log.json'):
    try:
        try:
            with open(log_path, 'r') as f:
                prev_logs = json.load(f)
        except FileNotFoundError:
            prev_logs = {}
        except json.JSONDecodeError:
            prev_logs = {}

        current_date = datetime.now().strftime("%Y-%m-%d")
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if current_date not in prev_logs:
            prev_logs[current_date] = [f"{current_time}  {message}"]
        else:
            prev_logs[current_date].append(f"{current_time}  {message}")
        
        with open(log_path, 'w') as f:
            json.dump(prev_logs, f, indent=4)

    except Exception as e:
        print(f"write_log failed at {datetime.now().strftime('%H:%M:%S')}: {e}")
        traceback.print_exc()