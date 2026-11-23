from datetime import datetime, timedelta, timezone

from flask import current_app


def now_str():
    tz = timezone(timedelta(hours=current_app.config["UTC_OFFSET_HOURS"]))
    return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")


def today_str():
    return now_str()[:10]
