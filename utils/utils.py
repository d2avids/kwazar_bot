import os
from datetime import datetime, timedelta

TIMEZONE_OFFSET = int(os.getenv('TIMEZONE_OFFSET', 0))


def get_current_datetime():
    """Возвращает текущее время в выбранной таймзоне."""
    return datetime.now() + timedelta(hours=TIMEZONE_OFFSET)


def adjust_datetime_for_scheduler(dt: datetime) -> datetime:
    """Корректирует время в зависимости от TIMEZONE_OFFSET для передачи в планировщик."""
    return dt - timedelta(hours=TIMEZONE_OFFSET)
