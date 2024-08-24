from utils import Utils

def place_order_sell(angel, symbol, token, qty, price):
	orderparams= {
				"variety": "NORMAL",
				"tradingsymbol": symbol,
				"symboltoken": token,
		        "exchange": "NFO",
		        "transactiontype": "SELL",
		        "quantity": qty,
		        "ordertype": "LIMIT",
		        "producttype": "CARRYFORWARD",
		        "price": Utils.roundToNSEPrice(price),
		        "duration": "DAY"
    			}
	OrderId = angel.placeOrder(orderparams)
	return OrderId

def place_order_buy(angel, symbol, token, qty, price):
	orderparams= {
				"variety": "NORMAL",
				"tradingsymbol": symbol,
				"symboltoken": token,
		        "exchange": "NFO",
		        "transactiontype": "BUY",
		        "quantity": qty,
		        "ordertype": "LIMIT",
		        "producttype": "CARRYFORWARD",
		        "price": Utils.roundToNSEPrice(price),
		        "duration": "DAY"
    			}
	OrderId = angel.placeOrder(orderparams)
	return OrderId

def sl_order(angel, symbol, qty, price):
	OrderId=angel.place_order(tradingsymbol=symbol,
								exchange=angel.EXCHANGE_NFO,
								transaction_type=angel.TRANSACTION_TYPE_BUY,
								quantity=qty,
								variety=angel.VARIETY_REGULAR,
								order_type=angel.ORDER_TYPE_SL,
								product=angel.PRODUCT_NRML,
								price=Utils.roundToNSEPrice(price+1),
								trigger_price=Utils.roundToNSEPrice(price))
	return OrderId

def modify_sl_order(angel,orderid,price,qty = None):
	OrderId = angel.modify_order(order_id=orderid,
									quantity=qty,
									variety=angel.VARIETY_REGULAR,
									order_type=angel.ORDER_TYPE_SL,
									price=Utils.roundToNSEPrice(price+1),
									trigger_price=Utils.roundToNSEPrice(price))
	return OrderId

def modify_order(angel,orderid,price,symbol=None,token=None,qty = None):
	modifyparams = {
			        "variety": "NORMAL",
			        "orderid": orderid,
			        "ordertype": "LIMIT",
			        "producttype": "CARRYFORWARD",
			        "duration": "DAY",
			        "price": Utils.roundToNSEPrice(price),
			        "quantity": qty,
			        "tradingsymbol": symbol,
			        "symboltoken": token,
			        "exchange": "NFO"
			        }
	OrderId = angel.modifyOrder(modifyparams)
	return OrderId

def cancel_order(angel,orderid):
	OrderId = angel.cancel_order(variety=angel.VARIETY_REGULAR, order_id=orderid)
	return OrderId

def modify_entry_order(angel,orderid,price,qty = None):
	OrderId = angel.modify_order(order_id=orderid,
									quantity=qty,
									variety=angel.VARIETY_REGULAR,
									order_type=angel.ORDER_TYPE_LIMIT,
									price=Utils.roundToNSEPrice(price))
	return OrderId
