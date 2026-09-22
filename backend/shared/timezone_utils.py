"""
Timezone utilities for SmartMaintain application.
Standardizes timezone handling across all services.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# Application timezone - Tunisia (UTC+1)
APP_TIMEZONE = ZoneInfo("Africa/Tunis")


def now_local():
    """
    Returns current datetime in application timezone (Africa/Tunis).
    Timezone-naive for database storage compatibility.
    """
    return datetime.now(APP_TIMEZONE).replace(tzinfo=None)


def now_utc():
    """
    Returns current datetime in UTC.
    Timezone-naive for database storage compatibility.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_to_local(dt):
    """
    Converts a UTC datetime to local timezone.
    
    Args:
        dt: datetime object (timezone-naive, assumed UTC)
    
    Returns:
        datetime object in local timezone (timezone-naive)
    """
    if dt is None:
        return None
    utc_dt = dt.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(APP_TIMEZONE)
    return local_dt.replace(tzinfo=None)


def local_to_utc(dt):
    """
    Converts a local datetime to UTC.
    
    Args:
        dt: datetime object (timezone-naive, assumed local)
    
    Returns:
        datetime object in UTC (timezone-naive)
    """
    if dt is None:
        return None
    local_dt = dt.replace(tzinfo=APP_TIMEZONE)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt.replace(tzinfo=None)


def format_iso_local(dt):
    """
    Formats datetime as ISO string with local timezone info.
    
    Args:
        dt: datetime object (timezone-naive, assumed local)
    
    Returns:
        ISO 8601 string with timezone
    """
    if dt is None:
        return None
    local_dt = dt.replace(tzinfo=APP_TIMEZONE)
    return local_dt.isoformat()
