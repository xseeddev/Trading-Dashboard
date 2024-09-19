# <------------------------------ Imports ------------------------------->

# System imports 
import traceback
import pandas as pd
from time import sleep
from typing import Tuple, Optional

# Project imports
from angel_broking import AngelBroking
from utils.trading.expiry import get_expiry


# <--------------------------------- Formats ------------------------------------->

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = f'{DATE_FORMAT} {TIME_FORMAT}'


# <------------------------------ Functions ------------------------------->

def get_token_info(
    df: pd.DataFrame, 
    strike_price: float, 
    option_type: str, 
    expiry_pref: int, 
    exch_seg: str = 'NFO', 
    instrument_type: str = 'OPTIDX', 
    symbol: str = 'NIFTY'
) -> Optional[Tuple[int, str]]:
    """
    Retrieve the option token and symbol based on the provided parameters.

    Parameters:
    - df (pd.DataFrame): DataFrame containing the option data.
    - strike_price (float): The strike price of the option.
    - option_type (str): The type of option (e.g., 'CE' or 'PE').
    - expiry_pref (str): The expiry preference, expected in the format DATE_FORMAT.
    - exch_seg (str): The exchange segment (default is 'NFO').
    - instrument_type (str): The type of instrument (default is 'OPTIDX').
    - symbol (str): The symbol of the instrument (default is 'NIFTY').

    Returns:
    - Optional[Tuple[int, str]]: A tuple containing the option token and symbol, or None if not found.
    """
    try:
        expiry_date: str = get_expiry(expiry_pref)
        info = df[
            (df['instrumenttype'] == instrument_type) & 
            (df['strike'] == float(strike_price * 100)) & 
            (df['expiry'] == expiry_date) & 
            (df['exch_seg'] == exch_seg) & 
            (df['name'] == symbol) & 
            (df['symbol'].str.endswith(option_type))
        ]

        if info.empty:
            print("No matching records found in the DataFrame.")
            return None
        
        df_info = info.iloc[0]
        option_token: int = df_info['token']
        option_sym: str = df_info['symbol']
        return option_token, option_sym

    except KeyError as e:
        print(f"Missing expected column in DataFrame: {e}")
    except Exception as e:
        print(f"An error occurred while retrieving token info: {e}")
    
    return None


def get_ltp(angel: AngelBroking, symbol: str, token: int, max_retries: int = 6, wait_time: int = 2) -> Optional[float]:
    """
    Fetches the last traded price (LTP) for a given symbol and token from the Angel Broking API.

    Args:
    - angel: The Angel Broking API instance.
    - symbol (str): The trading symbol for which to fetch the LTP.
    - token (str): The token associated with the symbol.
    - max_retries (int): The maximum number of retry attempts.
    - wait_time (int): The time to wait (in seconds) between retries.

    Returns:
    - Optional[float]: The last traded price if successful, None otherwise.
    """
    for attempt in range(max_retries):
        try:
            ltp_data = angel.user_instance.ltpData("NFO", symbol, token)
            ltp = ltp_data['data']['ltp']
            print(f"Successfully fetched LTP for {symbol}: {ltp}")
            return ltp
        except Exception as e:
            print(f"Failed to fetch LTP for {symbol}: {str(e)}")
            print(traceback.format_exc())
            sleep(wait_time)
            print(f"Retrying... ({attempt + 1}/{max_retries})")

    print("Max retries reached. LTP update failed for symbol: %s", symbol)
    return None


def update_nifty_ltp(angel: AngelBroking, max_attempts: int = 2) -> float:
    """
    Updates the last traded price (LTP) for the Nifty 50 index using Angel Broking API.

    Args:
    - angel (AngelBroking): The Angel Broking API instance.
    - max_attempts (int): The maximum number of retry attempts (default is 2).

    Returns:
    - float: The last traded price if successful, -1 if it fails after maximum attempts.
    """
    attempt_counter = 0
    
    while attempt_counter <= max_attempts:
        try:
            nifty_curr_market_price = angel.user_instance.ltpData("NSE", "Nifty 50", "99926000")['data']['ltp']
            print(f"Successfully fetched Nifty 50 LTP: {nifty_curr_market_price}")
            return float(nifty_curr_market_price)
        
        except Exception as e:
            print(f"Attempt {attempt_counter+1}: Failed to fetch Nifty 50 LTP: {str(e)}")
            print(traceback.format_exc())
            
            attempt_counter += 1
            if attempt_counter > max_attempts:
                print("Max attempts reached. Nifty 50 LTP update failed.")
                return -1
            
            print(f"Retrying LTP fetch... Attempt {attempt_counter}/{max_attempts}")
            sleep(2)


# <-------------------------------- END ------------------------------------->
