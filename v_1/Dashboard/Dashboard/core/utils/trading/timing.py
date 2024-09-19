# <--------------------------------- Imports ------------------------------------->

# System imports 
import csv
import holidays
import pandas as pd
from datetime import datetime, time


# <--------------------------------- Formats ------------------------------------->

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = f'{DATE_FORMAT} {TIME_FORMAT}'
holidays_file = 'data/holidays.csv'


# <-------------------------------- Logger ------------------------------------->


# <-------------------------------- Functions ------------------------------------->

def get_holidays_of_year(year: int = 2024, country: str = 'IN', save_path: str = 'data/holidays.csv') -> None:
    """
    Fetches all holidays for a given year and country, then stores them in a CSV file.

    Parameters:
    -----------
    year : int
        The year for which to retrieve holidays.
    country : str, optional
        The country code for which holidays are to be retrieved (default is 'US').
    save_path : str, optional
        The file path where the holiday data will be saved (default is 'data/holidays.csv').
    
    Returns:
    --------
    None
    
    Logs:
    -----
    - Logs the success or failure of the holiday retrieval and CSV saving.
    """
    try:
        country_holidays = holidays.CountryHoliday(country, years=[year])

        with open(save_path, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Holiday"])
            for date, name in sorted(country_holidays.items()):
                writer.writerow([date, name])

        print(f"Holidays for the year {year} saved successfully to {save_path}")

    except Exception as e:
        print(f"An error occurred while fetching or saving holidays: {e}")

def load_holidays(save_path: str = 'data/holidays.csv') -> set:
    """
    Reads the holiday data from a CSV file and returns it as a Pandas DataFrame.

    Parameters:
    -----------
    save_path : str, optional
        The file path from where the holiday data will be read (default is 'data/holidays.csv').
    
    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the holiday data.
    
    Logs:
    -----
    - Logs the success or failure of reading the CSV file.
    """
    try:
        holidays_df = pd.read_csv(save_path)
        holidays_df['Date'] = pd.to_datetime(holidays_df['Date'], format=DATE_FORMAT)
        holidays_df = holidays_df.drop(columns=['Holiday'])
        print(f"Holidays data loaded successfully from {save_path}")
        return holidays_df

    except FileNotFoundError:
        print(f"File not found at {save_path}. Please ensure the file exists.")
    except Exception as e:
        print(f"An error occurred while reading the holiday data: {e}")
    
    return pd.DataFrame()  # Return an empty DataFrame if any error occurs

def get_market_start_time() -> time:
    '''
        Get the market start time.

        Returns:
        - time: Market start time.
    '''
    return time(9, 15)

def get_market_end_time() -> time:
    '''
        Get the market end time.

        Returns:
        - time: Market end time.
    '''
    return time(15, 30)
    
def is_market_open(market_open_time='09:15:00', market_close_time='15:30:00', holidays_file='data/holidays.csv') -> bool:
    try:
        now = datetime.now()
        current_date = now.date()
        current_time = now.time()

        market_open = time.fromisoformat(market_open_time)
        market_close = time.fromisoformat(market_close_time)

        if now.weekday() >= 5:
            print(f"Today ({current_date}) is a weekend. Market is closed.")
            return False

        holidays_set = load_holidays(holidays_file)
        if current_date in holidays_set:
            print(f"Today ({current_date}) is a holiday. Market is closed.")
            return False

        if market_open <= current_time <= market_close:
            print(f"Market is open. Current time: {now.strftime(TIME_FORMAT)}.")
            return True
        else:
            print(f"Market is closed. Current time: {now.strftime(TIME_FORMAT)}.")
            return False

    except Exception as e:
        print(f"Error checking market status: {e}")
        return False


# <-------------------------------- END ------------------------------------->

# if __name__ == "__main__":
    # print(get_holidays_of_year())  # Get holidays
    # print(load_holidays())  # Get the set of holidays
    # print(get_market_start_time())  # Get the market start time
    # print(get_market_end_time())  # Get the market end time
    # print(is_market_open())  # Check if the market is open