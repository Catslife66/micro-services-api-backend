import datetime
from zoneinfo import ZoneInfo

def timestamp_to_datetime(timestamp):
    utc_dt = datetime.datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
    uk_dt = utc_dt.astimezone(ZoneInfo("Europe/London"))
    return uk_dt