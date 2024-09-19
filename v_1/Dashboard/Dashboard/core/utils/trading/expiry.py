# <--------------------------------- Imports ------------------------------------->

# System imports 
from datetime import datetime, timedelta

# Project imports
from utils.trading.timing import load_holidays, get_market_start_time, get_market_end_time


# <--------------------------------- Formats ------------------------------------->

DATE_FORMAT = '%Y-%m-%d'
TIME_FORMAT = '%H:%M:%S'
DATETIME_FORMAT = f'{DATE_FORMAT} {TIME_FORMAT}'


# <-------------------------------- Logger ------------------------------------->


# <-------------------------------- Functions ------------------------------------->

def get_week_expiry_day(date_obj=None, holidays=None) -> datetime:
    '''
        Get week expiry day for the given date.

        Args:
        - date_obj (datetime): Date object for which the expiry day is to be calculated.
        - holidays (set): Set of holidays.

        Returns:
        - datetime: Expiry day for the
    '''

    date_obj = date_obj or datetime.now()
    holidays = holidays or load_holidays()

    try:
        expiry_date = date_obj + timedelta(days=(3 - date_obj.weekday()) % 7)

        while expiry_date.date() in holidays:
            expiry_date += timedelta(days=7)

        return expiry_date.replace(hour=0, minute=0, second=0, microsecond=0)

    except Exception as e:
        print(f"Error calculating weekly expiry day: {e}")
        return None
    

def get_month_expiry_day(date_obj=None, holidays=None) -> datetime:
    '''
        Get month expiry day for the given date.

        Args:
        - date_obj (datetime): Date object for which the expiry day is to be calculated.
        - holidays (set): Set of holidays.

        Returns:
        - datetime: Expiry day for the
    '''

    date_obj = date_obj or datetime.now()
    holidays = holidays or load_holidays()

    try:
        next_month = (date_obj.replace(day=28) + timedelta(days=4)).replace(day=1)
        last_day = next_month - timedelta(days=1)

        expiry_date = last_day - timedelta(days=(last_day.weekday() - 3) % 7)

        while expiry_date.date() in holidays:
            expiry_date -= timedelta(days=7)

        return expiry_date.replace(hour=0, minute=0, second=0, microsecond=0)

    except Exception as e:
        print(f"Error calculating monthly expiry day: {e}")
        return None


def is_today_expiry(duration="week") -> bool:
    '''

        Args:
        - duration (str): Duration for which to check the expiry. 
            Allowed values: "week", "month"

        Returns:
    '''

    try:
        expiry_date = get_week_expiry_day() if duration == "week" else get_month_expiry_day()

        return datetime.now().date() == expiry_date.date()

    except Exception as e:
        return False
    

def get_expiry(num_weeks_plus=0) -> str:
    """
    Calculate the next expiry date for weekly stock derivatives, 
    considering the number of weeks to add and market opening hours.
    
    Args:
    - num_weeks_plus (int): Number of weeks to add to the current expiry date.
    
    Returns:
    - str: Expiry date in the format '18OCT2024'
    """

    expiry_date = get_week_expiry_day()

    if num_weeks_plus > 0:
        expiry_date += timedelta(weeks=num_weeks_plus)
        expiry_date = get_week_expiry_day(expiry_date)

    today_market_start_time = get_market_start_time()
    expiry_day_market_end_time = get_market_end_time()

    if today_market_start_time > expiry_day_market_end_time:
        expiry_date += timedelta(weeks=1)
        expiry_date = get_week_expiry_day(expiry_date)

    return expiry_date.strftime('%d%b%Y')


# <-------------------------------- END ------------------------------------->

# if __name__ == "__main__":
    # Test the get_week_expiry_day() function
    # print(get_week_expiry_day())
    # print(get_month_expiry_day())
    # print(is_today_expiry())
    # print(get_expiry(4))

    