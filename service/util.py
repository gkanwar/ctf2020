import datetime
import wsgiref.handlers as wsgihandlers
import time

def get_utc_now():
    return get_utc_timestamp(datetime.datetime.now())
def get_utc_past():
    return get_utc_timestamp(datetime.datetime.min)
def get_utc_timestamp(timestamp):
    now = time.mktime(timestamp.timetuple())
    return wsgihandlers.format_date_time(now)
