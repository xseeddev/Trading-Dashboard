# <--------------------------------- Imports ------------------------------------->

# System imports 
import traceback
import pandas as pd

# Project imports
from angel_broking import AngelBroking
from utils.token_info import get_ltp
from utils.math_functions import round_prices
from utils.orders.modify import handle_order_status, modify_order
from utils.trading.trades import prepare_trade_order, update_trade_dataframe, update_trade_status

# <--------------------------------- Functions ------------------------------------->

def base_order_parameters(transaction_type: str, price: float, symbol: str=None, token: int=None, quantity: int=None, order_id: int=None):
    params = {
        "variety": "NORMAL",
        "exchange": "NFO",
        "ordertype": "LIMIT",
        "producttype": "CARRYFORWARD",
        "duration": "DAY",
        "transactiontype": transaction_type,
        "price": round_prices.roundToNSEPrice(price),
        "tradingsymbol": symbol,
        "symboltoken": token,
        "quantity": quantity,
    }
    if order_id:
        params["orderid"] = order_id
    return params

def place_sell_order(angel: AngelBroking, symbol: str, token: int, quantity: int, price: float):
    order_params = base_order_parameters(
        transaction_type="SELL",
        price=round_prices.roundToNSEPrice(price),
        symbol=symbol,
        token=token,
        quantity=quantity
    )
    order_id = angel.user_instance.placeOrder(order_params)
    return order_id

def place_buy_order(angel: AngelBroking, symbol: str, token: int, quantity: int, price: float):
    order_params = base_order_parameters(
        transaction_type="BUY",
        price=round_prices.roundToNSEPrice(price),
        symbol=symbol,
        token=token,
        quantity=quantity
    )
    order_id = angel.user_instance.placeOrder(order_params)
    return order_id

def create_buy_order(angel: AngelBroking, buy_token: int, buy_symbol: str, buy_quantity: int):
    try:
        client = angel.user_object.name
        ltp = get_ltp(angel, buy_token, buy_symbol)
        buy_price = ltp + 0.5
        buy_order_id = place_buy_order(angel, buy_symbol, buy_token, buy_quantity, buy_price)
        return handle_order_status(angel, buy_order_id, "buy", buy_symbol, buy_token, client, modify_order)
    except Exception as e:
        print(f"{client}: buy_order execution failed")
        print(e)
        traceback.print_exc()
        return -1, -1, -1, -1
    
def create_sell_order(angel: AngelBroking, sell_token: int, sell_symbol: str, sell_quantity: int):
    try:
        client = angel.user_object.name
        ltp = get_ltp(angel, sell_token, sell_symbol)
        if ltp >= 1:
            ltp -= 0.5
        sell_order_id = place_sell_order(angel, sell_symbol, sell_token, sell_quantity, ltp)
        return handle_order_status(angel, sell_order_id, "sell", sell_symbol, sell_token, client, modify_order)
    except Exception as e:
        print(f"{client}: sell_order execution failed")
        print(e)
        traceback.print_exc()
        return -1, -1, -1, -1

def cancel_order(angel: AngelBroking, orderid: int):
	OrderId = angel.user_instance.cancelOrder(order_id=orderid)
	return OrderId

def order_execute(angel: AngelBroking, buy_strike: float, sell_strike: float, option_type: str, expiry: int) -> None:
    try:
        client = angel.user_object.name
        buy_token, buy_symbol, sell_token, sell_symbol, qty = prepare_trade_order(angel, buy_strike, sell_strike, option_type, expiry)
        if qty > 200:
            buy_sym, buy_qty, buy_price, buy_date = create_buy_order(angel, buy_token, buy_symbol, qty)
            
            if buy_sym == buy_symbol and buy_qty == qty:
                sell_sym, sell_qty, sell_price, sell_date = create_sell_order(angel, sell_token, sell_symbol, qty)

                if sell_sym == sell_symbol and abs(sell_qty) == qty:
                    update_trade_dataframe(angel, symbol=sell_symbol, token=sell_token, sell_price=sell_price, sell_date=sell_date, qty=sell_qty)
                    update_trade_dataframe(angel, symbol=buy_symbol, token=buy_token, buy_price=buy_price, buy_date=buy_date, qty=buy_qty)
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

def exit_active_trades(angel:AngelBroking) -> None:
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
        all_trades = pd.read_csv('trades.csv')
        client = angel.user_object.name

        all_active_trades: pd.DataFrame = all_trades[(all_trades['trade_status'] == 'ACTIVE') & (all_trades['client'] == client)]
        
        if all_active_trades.empty:
            print(f"{client}: No active trades to process.")
            return None
        
        all_active_trades = all_active_trades.sort_values(by='quantity')

        updated_trades = []

        for index, trade in all_active_trades.iterrows():
            result: list = []
            if trade['quantity'] < 0:
                try:
                    result = create_buy_order(angel, client, abs(trade['quantity']), trade['token'], trade['symbol'])
                    result.append('buy')
                except Exception as e:
                    print(f"{client}: Buy order failed for symbol {trade['symbol']}: {str(e)}")
                    print(f"Buy order failed for symbol {trade['symbol']}: {str(e)}")
                    traceback.print_exc()

            elif trade['quantity'] > 0:
                try:
                    result = create_sell_order(angel, client, abs(trade['quantity']), trade['token'], trade['symbol'])
                    result.append('sell')
                except Exception as e:
                    print(f"{client}: Sell order failed for symbol {trade['symbol']}: {str(e)}")
                    print(f"Sell order failed for symbol {trade['symbol']}: {str(e)}")
                    traceback.print_exc()

            if result:
                updated_trades.append((index, result))

        for index, result in updated_trades:
            all_trades = update_trade_status(all_trades, index, result)

        all_trades.to_csv('trades.csv', index=False)
        print(f"{client}: Trade processing completed successfully.")

    except Exception as e:
        print(f"{client}: Trade exit processing failed: {str(e)}")
        print(f"Trade exit processing failed: {str(e)}")
        traceback.print_exc()

# <--------------------------------- END ------------------------------------->