import datetime
import wsgiref.handlers as wsgihandlers
import time

def get_utc_now():
    return wsgihandlers.format_date_time(time.time())
def get_utc_past():
    return wsgihandlers.format_date_time(time.time() - 10*60)
