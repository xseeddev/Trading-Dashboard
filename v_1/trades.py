import utils
import orders
import traceback
import pandas as pd

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
        utils.write_log(f"Error updating trade status: {str(e)}")
        print(f"Error updating trade status: {str(e)}")
        traceback.print_exc()
        return dataframe

def exit_active_trades(angel, client):
    """
    Manage and exit all active trades for the specified client.
    
    1. Load all trades from the CSV file.
    2. Filter and sort active trades.
    3. Execute buy/sell orders based on trade quantity.
    4. Update trade status in the DataFrame.
    5. Save the updated DataFrame to the CSV file.
    """

    try:
        # Load trades from CSV
        all_trades = pd.read_csv('trades.csv')
        # Filter trades based on status and client
        all_active_trades = all_trades[(all_trades['trade_status'] == 'ACTIVE') & (all_trades['client'] == client)]
        
        if all_active_trades.empty:
            utils.write_log(f"{client}: No active trades to process.")
            return None
        
        all_active_trades = all_active_trades.sort_values(by='quantity')

        updated_trades = []

        for index, trade in all_active_trades.iterrows():
            result = None
            if trade['quantity'] < 0:
                # Execute buy order
                try:
                    result = orders.buy_order(angel, client, abs(trade['quantity']), trade['token'], trade['symbol'])
                    result.append('buy')
                except Exception as e:
                    utils.write_log(f"{client}: Buy order failed for symbol {trade['symbol']}: {str(e)}")
                    print(f"Buy order failed for symbol {trade['symbol']}: {str(e)}")
                    traceback.print_exc()

            elif trade['quantity'] > 0:
                # Execute sell order
                try:
                    result = orders.sell_order(angel, client, abs(trade['quantity']), trade['token'], trade['symbol'])
                    result.append('sell')
                except Exception as e:
                    utils.write_log(f"{client}: Sell order failed for symbol {trade['symbol']}: {str(e)}")
                    print(f"Sell order failed for symbol {trade['symbol']}: {str(e)}")
                    traceback.print_exc()

            if result:
                updated_trades.append((index, result))

        # Update DataFrame with the results
        for index, result in updated_trades:
            all_trades = update_trade_status(all_trades, index, result)

        # Save the updated DataFrame to CSV
        all_trades.to_csv('trades.csv', index=False)
        utils.write_log(f"{client}: Trade processing completed successfully.")

    except Exception as e:
        utils.write_log(f"{client}: Trade exit processing failed: {str(e)}")
        print(f"Trade exit processing failed: {str(e)}")
        traceback.print_exc()
