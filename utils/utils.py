from datetime import datetime
import pytz


def get_current_time_utc_plus_3():
    """Получить текущее московское время."""
    timezone_utc_plus_3 = pytz.timezone('Europe/Moscow')
    current_time_utc = datetime.now(pytz.utc)
    current_time_utc_plus_3 = current_time_utc.astimezone(timezone_utc_plus_3)
    return current_time_utc_plus_3
