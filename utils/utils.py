from datetime import datetime, timedelta
import os

TIMEZONE_OFFSET = int(os.getenv('TIMEZONE_OFFSET', 0))


def get_current_datetime():
    current_time = datetime.now()
    current_time_with_offset = current_time + timedelta(hours=TIMEZONE_OFFSET)
    return current_time_with_offset
