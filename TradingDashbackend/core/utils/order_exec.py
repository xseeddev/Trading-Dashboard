# This needs refactoring

from time import sleep
import traceback
from TradingDashbackend.core.utils import trade_utils
from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.master import TRADES_DF
from TradingDashbackend.core.utils import trade_user
from TradingDashbackend.core.utils.trade_utils import roundToNSEPrice, adjust_ltp



import traceback
import pandas as pd

# Project imports
from utils.token_info import get_ltp
from utils.math_functions import round_prices
from utils.orders.modify import handle_order_status, modify_order
from utils.trading.trades import prepare_trade_order, update_trade_dataframe, update_trade_status

logger = setup_logger("Core:Utils:Order Exec")


# <--------------------------------- Functions ------------------------------------->

def base_order_parameters(transaction_type: str, price: float, symbol: str=None, token: int=None, quantity: int=None, order_id: int=None):
    params = {
        "variety": "NORMAL",
        "exchange": "NFO",
        "ordertype": "LIMIT",
        "producttype": "CARRYFORWARD",
        "duration": "DAY",
        "transactiontype": transaction_type,
        "price": roundToNSEPrice(price),
        "tradingsymbol": symbol,
        "symboltoken": token,
        "quantity": quantity,
    }
    if order_id:
        params["orderid"] = order_id
    return params

def place_sell_order(angel_obj: trade_user, symbol: str, token: int, quantity: int, price: float):
    order_params = base_order_parameters(
        transaction_type="SELL",
        price=roundToNSEPrice(price),
        symbol=symbol,
        token=token,
        quantity=quantity
    )
    order_id = angel_obj.placeOrder(order_params)
    return order_id

def place_buy_order(angel_obj: trade_user, symbol: str, token: int, quantity: int, price: float):
    order_params = base_order_parameters(
        transaction_type="BUY",
        price=roundToNSEPrice(price),
        symbol=symbol,
        token=token,
        quantity=quantity
    )
    order_id = angel_obj.placeOrder(order_params)
    return order_id

def create_buy_order(angel_obj: trade_user, buy_token: int, buy_symbol: str, buy_quantity: int):
    try:
        client = angel_obj.Name
        ltp = get_ltp(angel_obj, buy_token, buy_symbol)
        buy_price = ltp + 0.5
        buy_order_id = place_buy_order(angel_obj, buy_symbol, buy_token, buy_quantity, buy_price)
        return handle_order_status(angel_obj, buy_order_id, "buy", buy_symbol, buy_token, client, modify_order)
    except Exception as e:
        print(f"{client}: buy_order execution failed")
        print(e)
        traceback.print_exc()
        return -1, -1, -1, -1
    
def create_sell_order(angel_obj: trade_user, sell_token: int, sell_symbol: str, sell_quantity: int):
    try:
        client = angel_obj.Name
        ltp = get_ltp(angel_obj, sell_token, sell_symbol)
        if ltp >= 1:
            ltp -= 0.5
        sell_order_id = place_sell_order(angel_obj, sell_symbol, sell_token, sell_quantity, ltp)
        return handle_order_status(angel_obj, sell_order_id, "sell", sell_symbol, sell_token, client, modify_order)
    except Exception as e:
        print(f"{client}: sell_order execution failed")
        print(e)
        traceback.print_exc()
        return -1, -1, -1, -1

def cancel_order(angel_obj: trade_user, orderid: int):
	OrderId = angel_obj.cancelOrder(order_id=orderid)
	return OrderId

def order_execute(angel_obj: trade_user, buy_strike: float, sell_strike: float, option_type: str, expiry: int) -> None:
    try:
        client = angel_obj.Name
        buy_token, buy_symbol, sell_token, sell_symbol, qty = trade_utils.trade_req(angel_obj, buy_strike, sell_strike, option_type, expiry)
        if qty > 200:
            buy_sym, buy_qty, buy_price, buy_date = create_buy_order(angel_obj, buy_token, buy_symbol, qty)
            
            if buy_sym == buy_symbol and buy_qty == qty:
                sell_sym, sell_qty, sell_price, sell_date = create_sell_order(angel_obj, sell_token, sell_symbol, qty)

                if sell_sym == sell_symbol and abs(sell_qty) == qty:
                    trade_utils.update_trade_dataframe(angel_obj, symbol=sell_symbol, token=sell_token, sell_price=sell_price, sell_date=sell_date, qty=sell_qty)
                    trade_utils.update_trade_dataframe(angel_obj, symbol=buy_symbol, token=buy_token, buy_price=buy_price, buy_date=buy_date, qty=buy_qty)
                    print(f"{client}: Complete order execution successful.")
                else:
                    print(f"{client}: Sell order execution failed.")
            else:
                print(f"{client}: Buy order execution failed.")
        else:
            print(f"{client}: Minimum margin requirement not fulfilled.")

    except Exception as e:
        print("Order execution failed for client %s: %s", client, str(e))
        print(traceback.format_exc())
        print("Order execution failed.")

def exit_active_trades(angel_obj:trade_user) -> None:
    """
    Manage and exit all active trades for the specified client.
    
    1. Load all trades from the CSV file.
    2. Filter and sort active trades.
    3. Execute buy/sell orders based on trade quantity.
    4. Update trade status in the DataFrame.
    5. Save the updated DataFrame to the CSV file.
    """

    # TODO: Implement the django setup and then test this
    try:
        all_trades = TRADES_DF
        client = angel_obj.Name

        all_active_trades: pd.DataFrame = all_trades[(all_trades['trade_status'] == 'ACTIVE') & (all_trades['client'] == client)]
        
        if all_active_trades.empty:
            logger.info(f"{client}: No active trades to process.")
            return None
        
        all_active_trades = all_active_trades.sort_values(by='quantity')

        updated_trades = []

        for index, trade in all_active_trades.iterrows():
            result: list = []
            if trade['quantity'] < 0:
                try:
                    result = create_buy_order(angel_obj, client, abs(trade['quantity']), trade['token'], trade['symbol'])
                    result.append('buy')
                except Exception as e:
                    logger.info(f"{client}: Buy order failed for symbol {trade['symbol']}: {str(e)}")
                    logger.debug(f"Buy order failed for symbol {trade['symbol']}: {str(e)}")
                    # traceback.print_exc()

            elif trade['quantity'] > 0:
                try:
                    result = create_sell_order(angel_obj, client, abs(trade['quantity']), trade['token'], trade['symbol'])
                    result.append('sell')
                except Exception as e:
                    logger.info(f"{client}: Sell order failed for symbol {trade['symbol']}: {str(e)}")
                    logger.debug(f"Sell order failed for symbol {trade['symbol']}: {str(e)}")
                    # traceback.print_exc()

            if result:
                updated_trades.append((index, result))

        for index, result in updated_trades:
            all_trades = trade_utils.update_trade_status(all_trades, index, result)

        # all_trades.to_csv('trades.csv', index=False)
        all_trades = TRADES_DF
        logger.info(f"{client}: Trade processing completed successfully.")

    except Exception as e:
        logger.info(f"{client}: Trade exit processing failed: {str(e)}")
        logger.debug(f"Trade exit processing failed: {str(e)}")
        # traceback.print_exc()

## Recheck If order status is allowed?

def handle_order_status(angel: trade_user, order_id: int, order_type: str, symbol: str, token: int, order_method=modify_order) -> dict:
    """Handle the order status and modify if necessary."""
    for _ in range(3):
        try:
            sleep(1)
            orderbook = angel.orderBook()
            orders = orderbook.get('data', [])
            
            for order in orders:
                if order['orderid'] == order_id:
                    result = process_order_status(angel, symbol, token, order, order_type, order_method)
                    if result is not None:
                        return result
            
            print(f"Order {order_id} failed.")
            return {-1, -1, -1, -1}

        except Exception as e:
            print(f"Orderbook calling failed, retrying...")

    print(f"Order {order_id} failed after multiple tries.")
    return {-1, -1, -1, -1}


def process_order_status(angel: trade_user, symbol: str, token: int, order, order_type: str, order_method=modify_order) -> dict:
    
    status = order['status']
    order_id = order['orderid']
    
    if status == 'open':
        try:
            ltp = angel.ltpData("NFO", symbol, token)['data']['ltp'] # Recheck
            unfilled_qty = float(order['unfilledshares'])
            adjusted_ltp = adjust_ltp(order_type, ltp)
            new_order_id = order_method(angel, order_id, adjusted_ltp, symbol, token, unfilled_qty)
            print(f"Order modified successfully: {new_order_id}")
            return new_order_id
        except Exception as e:
            print(f"Order modification failed: {str(e)}")
            return None

    elif status == 'complete':
        try:
            symbol = order['tradingsymbol']
            quantity = float(order['quantity'])
            price = order['averageprice']
            date = order['updatetime']
            print(f"Order executed successfully: {symbol}, {quantity}, {price}, {date}")
            return {symbol, quantity, price, date}
        except Exception as e:
            print(f"Order execution failed: {str(e)}")
            return {-1, -1, -1, -1}

    elif status in ['rejected', 'cancelled']:
        print(f"Order {order_id} {status} due to {order['message']}")
        return {-1, -1, -1, -1}

    return None

# <--------------------------------- END ------------------------------------->