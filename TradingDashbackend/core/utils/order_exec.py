from time import sleep
import traceback
from TradingDashbackend.core.utils import trade_utils
from TradingDashbackend.core.logger import setup_logger
from TradingDashbackend.core.master import TRADES_DF

logger = setup_logger("Core:Utils:Order Exec")
# Pending Fix

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
		        "price": trade_utils.roundToNSEPrice(price),
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
		        "price": trade_utils.roundToNSEPrice(price),
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
			        "price": trade_utils.roundToNSEPrice(price),
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

def cancel_order(angel_obj, inputparams):
	
    # inputparams = [{
	#   "orderid":order_id
    #   "client":client,
    # }]

    orderid = inputparams['orderid']
    client = inputparams['client']

    try:
        OrderId = angel_obj.cancel_order(variety=angel_obj.VARIETY_REGULAR, order_id=orderid)
        logger.info("Cancelled Order, id:"+OrderId)
    except:
        logger.info("Error in Cancelling Order,Id:",OrderId)

    return OrderId

def modify_entry_order(angel_obj, inputparams):
    
    # inputparams = [{
	#   "orderid":order_id
    #   "client":client,
	# 	"symbol":sell_symbol,
	# 	"token":sell_token,
	# 	"qty":sell_qty,
	# 	"price":sell_ltp
    # }]
	
    orderid = inputparams['orderid']
    qty = inputparams["qty"]
    price = inputparams["price"]
    client = inputparams['client']

    try:
        OrderId = angel_obj.modify_order(order_id=orderid,
                                    quantity=qty,
                                    variety=angel_obj.VARIETY_REGULAR,
                                    order_type=angel_obj.ORDER_TYPE_LIMIT,
                                    price=trade_utils.roundToNSEPrice(price))
        logger.info("Modified Order, id:"+OrderId)
    except:
        logger.info("Error in Modifying Order,Id:",OrderId)

    return OrderId

# To FIx |
#        v 

def buy_order(angel, client, buy_qty, buy_token, buy_symbol):
    
    try:
        buy_ltp = trade_utils.call_ltp(angel, buy_symbol, buy_token)

        inputparams = [{
            "client":client,
            "symbol":buy_symbol,
            "token":buy_token,
            "qty":buy_qty,
            "price":buy_ltp+0.5
        }]

        buy_Orderid = place_order_buy(angel, inputparams)
        i=0
        while True:
            try:
                sleep(1)
                orderbook = angel.orderBook()
                buy_rec = orderbook['data']
                for buy_row in buy_rec:
                    if i < 3:
                        if (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'open'):
                            try:
                                buy_ltp = angel.ltpData("NFO", buy_symbol, buy_token)['data']['ltp']
                                m_qty = int(buy_row['unfilledshares'])

                                inputparams = [{
                                    "orderid":buy_Orderid,
                                    "client":client,
                                    "symbol":buy_symbol,
                                    "token":buy_token,
                                    "qty":m_qty,
                                    "price":buy_ltp+0.5
                                }]

                                buy_modify_Orderid = modify_order(angel, inputparams)
                                i=i+1
                                logger.info(client + ": buy_order modified as price skipped")
                            except:
                                i=i+1
                                traceback.print_exc()
                                logger.info(client + ": buy_modify_order failed")

                        elif (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'complete'):
                            try:
                                buy_symbol = buy_row['tradingsymbol']
                                buy_qty = int(buy_row['quantity'])
                                buy_price = buy_row['averageprice']
                                buy_date = buy_row['updatetime']
                                logger.info(client + ": buy_leg_order placed successfully")
                                return buy_symbol, buy_qty, buy_price, buy_date
                            except:
                                logger.info(client + ": buy_order executed, but orderbook calling failed")
                                logger.debug("buy_order executed, but orderbook calling failed"+traceback.print_exc())
                                
                                return -1, -1, -1, -1

                        elif (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'rejected'):
                            logger.info(client + ": buy_order_placement_rejected")
                            return -1, -1, -1, -1

                        elif (buy_row['orderid'] == buy_Orderid) and (buy_row['status'] == 'cancelled'):
                            logger.info(client + ": buy_order_placement_cancelled")
                            return -1, -1, -1, -1

                    else:
                        logger.info(client + ": buy_order_placement_failed")
                        return -1, -1, -1, -1
            except:
                logger.info(client + ": orderbook calling for buy leg failed, retrying...")
                logger.debug("orderbook calling 4r buy leg failed, retrying..."+traceback.print_exc()) 
    except:
        logger.info(client + ": buy_order exe failed")
        logger.debug("buy_order exe failed" + traceback.print_exc())

def sell_order(angel, client, sell_qty, sell_token, sell_symbol):
    

    try:
        sell_ltp = trade_utils.call_ltp(angel, sell_symbol, sell_token)
        if sell_ltp >= 1: sell_ltp = sell_ltp-0.5

        inputparams = [{
            "client":client,
            "symbol":sell_symbol,
            "token":sell_token,
            "qty":sell_qty,
            "price":sell_ltp
        }]
        
        sell_Orderid = place_order_sell(angel, inputparams)
        i=0
        while True:
            try:
                sleep(1)
                orderbook = angel.orderBook()
                sell_rec = orderbook['data']
                for sell_row in sell_rec:
                    if i < 3:
                        if (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'open'):
                            try:
                                sell_ltp = angel.ltpData("NFO", sell_symbol, sell_token)['data']['ltp']
                                if sell_ltp >= 1: sell_ltp = sell_ltp-0.5
                                m_qty = int(sell_row['unfilledshares'])
                                sell_modify_Orderid = modify_order(angel, sell_Orderid, sell_ltp, sell_symbol, sell_token, m_qty)
                                i=i+1
                                logger.info(client + ": sell_order modified as price skipped")
                            except:
                                i=i+1
                               
                                logger.info(client + ": sell_modify_order failed")

                        elif (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'complete'):
                            try:
                                sell_symbol = sell_row['tradingsymbol']
                                sell_qty = int(sell_row['quantity'])
                                sell_price = sell_row['averageprice']
                                sell_date = sell_row['updatetime']
                                logger.info(client + ": sell_leg_order placed successfully")
                                return sell_symbol, sell_qty, sell_price, sell_date
                            except:
                                logger.info(client + ": sell_order executed, but orderbook calling failed")
                                logger.debug("sell_order executed, but orderbook calling failed" + traceback.print_exc())
                                
                                return -1, -1, -1, -1

                        elif (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'rejected'):
                            logger.info(client + ": sell_order_placement_rejected")
                            return -1, -1, -1, -1

                        elif (sell_row['orderid'] == sell_Orderid) and (sell_row['status'] == 'cancelled'):
                            logger.info(client + ": sell_order_placement_cancelled")
                            return -1, -1, -1, -1
                    else:
                        logger.info(client + ": sell_order_placement_failed")
                        logger.debug("sell_order_placement_failed")
                        return -1, -1, -1, -1
            except:
                logger.info(client + ": orderbook calling 4r sell leg failed, retrying...")
                logger.debug("orderbook calling 4r sell leg failed, retrying..." + traceback.print_exc())  
    except:
        logger.info(client + ": sell_order exe failed")
        logger.debug("sell_order exe failed" + traceback.print_exc())
        

def new_trade_exec(inputparams):

    # inputparams = [{
    #     "angel_obj":angel,
    #     "client":client,
    #     "buy_strike":buy_strike,
    #     "sell_strike":sell_strike,
    #     "option_type":option_type,
    #     "expiry":expiry
    # }]
    
    angel = inputparams["angel_obj"]
    client = inputparams["client"]
    buy_strike = inputparams["buy_strike"]
    sell_strike = inputparams["sell_strike"]
    option_type = inputparams["option_type"]
    expiry = inputparams["expiry"]

    try:
        buy_token, buy_symbol, sell_token, sell_symbol, qty = trade_utils.trade_req(angel, client, buy_strike, sell_strike, option_type, expiry)
        if qty>200:
            buy_sym, buy_qty, buy_price, buy_date = buy_order(angel, client, qty, buy_token, buy_symbol)
            if buy_sym==buy_symbol and buy_qty==qty:
                sell_sym, sell_qty, sell_price, sell_date = sell_order(angel, client, qty, sell_token, sell_symbol)
                if sell_sym==sell_symbol and abs(sell_qty)==qty:
                    trade_utils.update_trade_dataframe(client=client, symbol=sell_symbol, qty=-(sell_qty), sell_price=sell_price, token=sell_token, sell_date=sell_date)
                    trade_utils.update_trade_dataframe(client=client, symbol=buy_symbol, qty=buy_qty, buy_price=buy_price, token=buy_token, buy_date=buy_date)
                    logger.info(client + ": complete order exe successfull")
        else:
           logger.info(client + ": min. margin req. not fullfilled")
    except:
        logger.info(client + ": NEW TRADE exe failed")
        logger.debug("order exe failed" + traceback.print_exc())
    
def exit_trade_exec(inputparams):
    # inputparams = [{
    #     "angel_obj":angel,
    #     "client":client,
    # }]
    
    angel = inputparams["angel_obj"]
    client = inputparams["client"]

    try:
        df = TRADES_DF

        active_legs = df[(df['leg_status'] != 'CLOSED') & (df['client'] == client)]
        active_legs = active_legs.sort_values(by='qty')

        for index, row in active_legs.iterrows():

            if row['qty'] < 0 :
                buy_symbol, buy_qty, buy_price, buy_date = buy_order(angel, abs(row['qty']), row['token'], row['symbol'])
                df.at[index, 'buy_price'] = buy_price
                df.at[index, 'buy_date'] = buy_date
                df.at[index, 'qty'] = abs(buy_qty)
                df.at[index, 'leg_status'] = 'CLOSED'
                df.at[index, 'leg_pnl'] = ((df.at[index, 'sell_price']-buy_price)*df.at[index, 'qty'])

            elif row['qty'] > 0 :
                sell_symbol, sell_qty, sell_price, sell_date = sell_order(angel, abs(row['qty']), row['token'], row['symbol'])
                df.at[index, 'sell_price'] = sell_price
                df.at[index, 'sell_date'] = sell_date
                df.at[index, 'qty'] = abs(sell_qty)
                df.at[index, 'leg_status'] = 'CLOSED'
                df.at[index, 'leg_pnl'] = (sell_price-df.at[index, 'buy_price'])*df.at[index, 'qty']

        active_legs = df[(df['leg_status'] != 'CLOSED') & (df['client'] == client)]
        if not active_legs.empty:
            logger.info(client + ": trade still open")
            logger.debug("Trade Still open" + TRADES_DF)
        else:
            logger.info(client + ": trade exit completed successfully")
    except:
        Utils.write_log(client + ": trade exit failed")
        print("\n" + client +": trade_exit exe failed")
        traceback.print_exc()

def auto_exit_trade_exec(inputparams):
     
    # inputparams = [{
    #     "angel_obj":angel,
    #     "client":client,
    #     "trade_params":{}
    # }]
    
    angel_obj = inputparams["angel_obj"]
    client = inputparams["client"]
    trade_params = inputparams["trade_params"]

    while True:
        nf_ltp = trade_utils.update_nf_ltp(angel_obj)
        if nf_ltp != -1:
            if trade_params['option_type'] == 'CE':
                if nf_ltp > trade_params['nf_sl'] or nf_ltp < trade_params['nf_target']:
                    params = [{
                        "angel_obj":angel_obj,
                        "client":client,
                    }]
                    exit_trade_exec(params)
                    break
            elif trade_params['option_type'] == 'PE':
                if nf_ltp < trade_params['nf_sl'] or nf_ltp > trade_params['nf_target']:
                    params = [{
                        "angel_obj":angel_obj,
                        "client":client,
                    }]
                    exit_trade_exec(params)
                    break