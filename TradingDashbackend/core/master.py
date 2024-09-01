import pandas as pd
from TradingDashbackend.core.logger import setup_logger

logger = setup_logger("Core Master")
TRADES_DF = pd.DataFrame(columns=['client', 'symbol', 'token', 'buy_date', 'buy_price', 'qty', 'sell_price', 'sell_date', 'leg_status', 'leg_pnl'])
SCRIPTS_MASTER_DF = pd.DataFrame()