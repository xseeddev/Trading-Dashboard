# <--------------------------------- Imports ------------------------------------->

# System imports 
import datetime
import traceback
import pandas as pd
from typing import Tuple, Optional

# Project imports
from angel_broking import AngelBroking
from ..token_info import get_token_info

# <-------------------------------- Logger ------------------------------------->


# <-------------------------------- Functions ------------------------------------->

def prepare_trade_order(
    angelInstance: AngelBroking, 
    buy_leg_strike: float, 
    sell_leg_strike: float, 
    option_type: str, 
    expiry: int
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[int]]:
    """
    Prepare the details needed for placing a trade order based on user and option details.

    Parameters:
    - user (User): The user object with methods to get available margin and required margin.
    - buy_leg_strike (float): The strike price for the buy leg of the trade.
    - sell_leg_strike (float): The strike price for the sell leg of the trade.
    - option_type (str): The type of option (e.g., 'CE' or 'PE').
    - expiry (str): The expiry date preference for the options.

    Returns:
    - Tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[int]]:
      A tuple containing:
        - Buy leg token
        - Buy leg symbol
        - Sell leg token
        - Sell leg symbol
        - Quantity to trade
    """
    try:
        client = angelInstance.user_object.name
        dataframe_all_tokens = angelInstance.get_all_tokens_tradable()
        buy_leg_token, buy_leg_symbol = get_token_info(
            df=dataframe_all_tokens, 
            strike_price=buy_leg_strike, 
            option_type=option_type, 
            expiry_pref=expiry
        )
        sell_leg_token, sell_leg_symbol = get_token_info(
            df=dataframe_all_tokens, 
            strike_price=sell_leg_strike, 
            option_type=option_type, 
            expiry_pref=expiry
        )

        avail_margin = angelInstance.user_object.get_available_margin()
        margin_per_lot = angelInstance.user_object.get_required_margin(buy_leg_token, sell_leg_token)

        if margin_per_lot <= 0:
            print(f"{client}: Margin per lot is non-positive, cannot compute lots.")
            return None, None, None, None, None

        # Calculate the number of lots and quantity
        lots = int(avail_margin / margin_per_lot)
        qty = lots * 25
        
        print(f"{client}: Trade order prepared successfully")
        return buy_leg_token, buy_leg_symbol, sell_leg_token, sell_leg_symbol, qty

    except Exception as e:
        print(f"{client}: Failed to prepare trade order - {str(e)}")
        print(f"{client}: Trade order preparation failed", exc_info=True)
        return None, None, None, None, None

def update_trade_dataframe(
    angel: AngelBroking,
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
        client = angel.user_object.name
        columns = ['client', 'symbol', 'token', 'buy_date', 'buy_price', 'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl']
        new_row = pd.Series([client, symbol, token, buy_date, buy_price, qty, sell_price, sell_date, leg_status, leg_pnl], index=columns)

        df = pd.read_csv('trades.csv')
        df = df.append(new_row, ignore_index=True)
        df.to_csv('trades.csv', index=False)

        print("Trade data updated successfully for client: %s", client)

    except Exception as e:
        print("Failed to update trade CSV for client %s: %s", client, str(e))
        print(f"\nTrade CSV update failed @ {datetime.now().strftime('%H:%M:%S')}")

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
        print(f"Error updating trade status: {str(e)}")
        print(f"Error updating trade status: {str(e)}")
        traceback.print_exc()
        return dataframe


def delete_closed_trades(trades_df):
    # TODO: Try this once the django setup is done
    """
    Deletes trades from the DataFrame that have 'CLOSED' status in the 'leg_status' column.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades information.
        
    Returns:
        pd.DataFrame: Updated DataFrame with closed trades removed.
    """
    try:
        closed_trades = trades_df[trades_df['leg_status'] == 'CLOSED']

        if not closed_trades.empty:
            updated_trades_df = trades_df.drop(closed_trades.index)
            print(f"Deleted {len(closed_trades)} closed trades successfully.")
            return updated_trades_df
        else:
            print("No closed trades found to delete.")
            return trades_df

    except Exception as e:
        print(f"Failed to delete closed trades: {str(e)}")
        print(traceback.format_exc())
        return trades_df