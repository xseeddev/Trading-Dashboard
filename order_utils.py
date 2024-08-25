from utils import Utils
from logger import setup_logger

logger = setup_logger("Order Execution Utils")

def place_order_sell(angel_obj, inputparams):

	# inputparams = [{
    #   "client":client,
	# 	"symbol":sell_symbol,
	# 	"token":sell_token,
	# 	"qty":sell_qty,
	# 	"price":sell_ltp
    # }]

	symbol = inputparams["symbol"]
	token = inputparams["token"]
	qty = inputparams["qty"]
	price = inputparams["price"]
	client = inputparams['client']

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
	try:
		OrderId = angel_obj.placeOrder(orderparams)
		logger.info(client+":Placed Order, id:"+OrderId)
	except:
		logger.info("Error in Placing Order sell, Client:"+client)

	return OrderId

def place_order_buy(angel_obj, inputparams):
	# inputparams = [{
    #   "client":client,
	# 	"symbol":sell_symbol,
	# 	"token":sell_token,
	# 	"qty":sell_qty,
	# 	"price":sell_ltp
    # }]

	symbol = inputparams["symbol"]
	token = inputparams["token"]
	qty = inputparams["qty"]
	price = inputparams["price"]
	client = inputparams['client']

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

	try:
		OrderId = angel_obj.placeOrder(orderparams)
		logger.info(client+":Placed Order, id:"+OrderId)
	except:
		logger.info("Error in Placing Order Buy, Client:"+client)
	return OrderId

def modify_order(angel_obj,inputparams):
	# inputparams = [{
	#   "orderid":order_id
    #   "client":client,
	# 	"symbol":sell_symbol,
	# 	"token":sell_token,
	# 	"qty":sell_qty,
	# 	"price":sell_ltp
    # }]

	orderid = inputparams['orderid']
	symbol = inputparams["symbol"]
	token = inputparams["token"]
	qty = inputparams["qty"]
	price = inputparams["price"]
	client = inputparams['client']



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
	try:
		OrderId = angel_obj.placeOrder(modifyparams)
		logger.info(client+":Modified Order, id:"+OrderId)
	except:
		logger.info("Error in Modifying Order, Client:"+client)
	return OrderId

def cancel_order(angel_obj,orderid):
	OrderId = angel_obj.cancel_order(variety=angel_obj.VARIETY_REGULAR, order_id=orderid)

	try:
		OrderId = angel_obj.cancel_order(variety=angel_obj.VARIETY_REGULAR, order_id=orderid)
		logger.info("Cancelled Order, id:"+OrderId)
	except:
		logger.info("Error in Cancelling Order,Id:",OrderId)

	return OrderId

def modify_entry_order(angel,orderid,price,qty = None):
	OrderId = angel.modify_order(order_id=orderid,
									quantity=qty,
									variety=angel.VARIETY_REGULAR,
									order_type=angel.ORDER_TYPE_LIMIT,
									price=Utils.roundToNSEPrice(price))
	return OrderId
