'''
    Action: execute API calls to place orders.
'''
import utils
import traceback
from time import sleep

# <------------------------------- Helper functions -------------------------------------->

def adjust_ltp(order_type, ltp):
    if order_type == 'buy':
        return ltp + 0.5
    elif order_type == 'sell' and ltp >= 1:
        return ltp - 0.5
    return ltp

def log_status(client, order_type, message, exception=None):
    if exception:
        utils.write_log(f"{client}: {order_type}_{message} failed")
        print(exception)
        traceback.print_exc()
    else:
        utils.write_log(f"{client}: {order_type}_{message}")


def base_order_parameters(transaction_type, price, symbol=None, token=None, quantity=None, order_id=None):
    params = {
        "variety": "NORMAL",
        "exchange": "NFO",
        "ordertype": "LIMIT",
        "producttype": "CARRYFORWARD",
        "duration": "DAY",
        "price": utils.roundToNSEPrice(price),
        "quantity": quantity,
        "tradingsymbol": symbol,
        "symboltoken": token,
        "transactiontype": transaction_type,
    }
    if order_id:
        params["orderid"] = order_id
    return params

# <------------------------------- Place Order -------------------------------------->

def place_sell_order(angel, symbol, token, quantity, price):
    order_params = base_order_parameters(
        transaction_type="SELL",
        price=price,
        symbol=symbol,
        token=token,
        quantity=quantity
    )
    order_id = angel.placeOrder(order_params)
    return order_id

def place_buy_order(angel, symbol, token, quantity, price):
    order_params = base_order_parameters(
        transaction_type="BUY",
        price=price,
        symbol=symbol,
        token=token,
        quantity=quantity
    )
    order_id = angel.placeOrder(order_params)
    return order_id

def modify_order(angel, order_id, price, symbol=None, token=None, quantity=None):
    modify_params = base_order_parameters(
        transaction_type=None,
        price=price,
        symbol=symbol,
        token=token,
        quantity=quantity,
        order_id=order_id
    )
    order_id = angel.modifyOrder(modify_params)
    return order_id

def cancel_order(angel, order_id):
	order_id = angel.cancel_order(variety=angel.VARIETY_REGULAR, order_id=order_id)
	return order_id


# <------------------------------- Place Stop loss orders -------------------------------------->

def base_stop_loss_order_params(angel, price, quantity=None, order_id=None):
    params = {
        "variety": angel.VARIETY_REGULAR,
        "order_type": angel.ORDER_TYPE_SL,
        "product": angel.PRODUCT_NRML,
        "price": utils.roundToNSEPrice(price + 1),
        "trigger_price": utils.roundToNSEPrice(price),
        "quantity": quantity,
        "exchange": angel.EXCHANGE_NFO,
        "transaction_type": angel.TRANSACTION_TYPE_BUY,
    }
    if order_id:
        params["order_id"] = order_id
    return params

def place_stop_loss_order(angel, symbol, quantity, price):
    order_params = base_stop_loss_order_params(angel, price, quantity)
    order_params["tradingsymbol"] = symbol
    order_id = angel.place_order(**order_params)
    return order_id

def modify_stop_loss_order(angel, order_id, price, quantity=None):
    modify_params = base_stop_loss_order_params(angel, price, quantity, order_id)
    order_id = angel.modify_order(**modify_params)
    return order_id


# <------------------------------- Orders -------------------------------------->

def buy_order(angel, client, buy_token, buy_symbol, buy_quantity):
    try:
        ltp = utils.get_ltp(angel, buy_token, buy_symbol)
        buy_price = ltp + 0.5
        buy_order_id = place_buy_order(angel, buy_symbol, buy_token, buy_quantity, buy_price)
        return handle_order_status(angel, buy_order_id, "buy", buy_symbol, buy_token, client, modify_order)
    except Exception as e:
        utils.write_log(f"{client}: buy_order execution failed")
        print(e)
        traceback.print_exc()
        return -1, -1, -1, -1

def sell_order(angel, client,sell_token, sell_symbol, sell_quantity):
    try:
        ltp = utils.get_ltp(angel, sell_token, sell_symbol)
        if ltp >= 1:
            ltp -= 0.5
        sell_order_id = place_sell_order(angel, sell_symbol, sell_token, sell_quantity, ltp)
        return handle_order_status(angel, sell_order_id, "sell", sell_symbol, sell_token, client, modify_order)
    except Exception as e:
        utils.write_log(f"{client}: sell_order execution failed")
        print(e)
        traceback.print_exc()
        return -1, -1, -1, -1

def process_order_status(angel, order, order_type, symbol, token, client, order_method):
    """Process and modify order status based on the current state."""
    status = order['status']
    order_id = order['orderid']
    
    if status == 'open':
        try:
            ltp = angel.ltpData("NFO", symbol, token)['data']['ltp']
            adjusted_ltp = adjust_ltp(order_type, ltp)
            unfilled_qty = int(order['unfilledshares'])
            new_order_id = order_method(angel, order_id, adjusted_ltp, symbol, token, unfilled_qty)
            log_status(client, order_type, "order modified with id:" + str(new_order_id) + " as price skipped")
            return new_order_id
        except Exception as e:
            log_status(client, order_type, "modify_order", e)
            return None

    elif status == 'complete':
        try:
            symbol = order['tradingsymbol']
            quantity = int(order['quantity'])
            price = order['averageprice']
            date = order['updatetime']
            log_status(client, order_type, "leg_order placed successfully")
            return {symbol, quantity, price, date}
        except Exception as e:
            log_status(client, order_type, "order executed, but orderbook calling failed", e)
            return {-1, -1, -1, -1}

    elif status in ['rejected', 'cancelled']:
        log_status(client, order_type, f"order_placement_{status}")
        return {-1, -1, -1, -1}

    return None

def handle_order_status(angel, order_id, order_type, symbol, token, client, order_method):
    """Handle the order status and modify if necessary."""
    for _ in range(3):
        try:
            sleep(1)
            orderbook = angel.orderBook()
            orders = orderbook.get('data', [])
            
            for order in orders:
                if order['orderid'] == order_id:
                    result = process_order_status(angel, order, order_type, symbol, token, client, order_method)
                    if result is not None:
                        return result
            
            log_status(client, order_type, "order_placement_failed")
            return {-1, -1, -1, -1}

        except Exception as e:
            log_status(client, order_type, "orderbook calling failed, retrying...", e)

    log_status(client, order_type, "orderbook calling failed after retries")
    return {-1, -1, -1, -1}