# <--------------------------------- Imports ------------------------------------->

# System imports 
import traceback
from time import sleep

# Project imports 
from angel_broking import AngelBroking
from utils.math_functions import round_prices


# <--------------------------------- Functions ------------------------------------->

# Helper function
def adjust_ltp(order_type: str, ltp: float) -> float:
    if order_type == 'buy':
        return ltp + 0.5
    elif order_type == 'sell' and ltp >= 1:
        return ltp - 0.5
    return ltp


def modify_order(angel: AngelBroking, order_id: int, price: float, symbol: str, token: str, qty: int) -> dict:
    """
    Modifies an existing order in the Angel Broking API.

    Args:
    - angel: The Angel Broking API instance.
    - order_id (str): The ID of the order to modify.
    - price (float): The new price for the order.
    - symbol (str, optional): The trading symbol associated with the order.
    - token (str, optional): The token associated with the trading symbol.
    - qty (int, optional): The new quantity for the order.

    Returns:
    - dict: The response from the API after modifying the order.
    """

    modify_params = {
        "variety": "NORMAL",
        "orderid": order_id,
        "ordertype": "LIMIT",
        "producttype": "CARRYFORWARD",
        "duration": "DAY",
        "price": round_prices.roundToNSEPrice(price),
        "quantity": qty,
        "tradingsymbol": symbol,
        "symboltoken": token,
        "exchange": "NFO"
    }

    try:
        response = angel.user_instance.modifyOrder(modify_params)
        print("Order modified successfully: %s", response)
        return response

    except Exception as e:
        print("Failed to modify order %s: %s", order_id, str(e))
        return {"success": False, "error": str(e)}
    
    
# <--------------------------------- STOP LOSS ------------------------------------->
def base_stop_loss_order_params(angel: AngelBroking, price: float, quantity: int, order_id: int=None) -> dict:
    params = {
        "variety": angel.user_instance.VARIETY_REGULAR,
        "order_type": angel.user_instance.ORDER_TYPE_SL,
        "product": angel.user_instance.PRODUCT_NRML,
        "price": round_prices.roundToNSEPrice(price + 1),
        "trigger_price": round_prices.roundToNSEPrice(price),
        "quantity": quantity,
        "exchange": angel.user_instance.EXCHANGE_NFO,
        "transaction_type": angel.user_instance.TRANSACTION_TYPE_BUY,
    }
    if order_id:
        params["order_id"] = order_id
    return params


def place_stop_loss_order(angel: AngelBroking, symbol: str, quantity: int, price: float):
    order_params = base_stop_loss_order_params(angel, price, quantity)
    order_params["tradingsymbol"] = symbol
    order_id = angel.user_instance.placeOrder(**order_params)
    return order_id


def modify_stop_loss_order(angel: AngelBroking, order_id: int, price: float, quantity: int=None):
    modify_params = base_stop_loss_order_params(angel, price, quantity, order_id)
    order_id = modify_order(**modify_params)
    return order_id


def process_order_status(angel: AngelBroking, symbol: str, token: int, order, order_type: str, order_method=modify_order) -> dict:
    
    status = order['status']
    order_id = order['orderid']
    
    if status == 'open':
        try:
            ltp = angel.user_instance.ltpData("NFO", symbol, token)['data']['ltp']
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


def handle_order_status(angel: AngelBroking, order_id: int, order_type: str, symbol: str, token: int, order_method=modify_order) -> dict:
    """Handle the order status and modify if necessary."""
    for _ in range(3):
        try:
            sleep(1)
            orderbook = angel.user_instance.orderBook()
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

# <--------------------------------- END ------------------------------------->