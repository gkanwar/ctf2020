import datetime
import wsgiref.handlers as wsgihandlers
import time

def get_utc_now():
    return wsgihandlers.format_date_time(time.time())
def get_utc_past():
    return wsgihandlers.format_date_time(time.time() - 10*60)
def get_utc_future(dt):
    return wsgihandlers.format_date_time(time.time() + dt)
