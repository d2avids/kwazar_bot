from datetime import datetime, timedelta


def get_current_time_utc_plus_3() -> datetime:
    """Получить текущее московское время."""
    current_time_utc = datetime.now()
    current_time_utc_plus_3 = current_time_utc + timedelta(hours=3)
    return current_time_utc_plus_3
