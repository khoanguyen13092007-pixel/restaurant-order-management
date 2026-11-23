import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "restaurant.db"))
    # Hết phiên sau thời gian không hoạt động (đặc tả chưa chốt con số, tạm 30 phút)
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Bật True khi triển khai sau HTTPS
    SESSION_COOKIE_SECURE = False
    # Thuế áp dụng cho hoá đơn: thiết kế GUI ghi Tax (10%)
    TAX_RATE = float(os.environ.get("TAX_RATE", "0.10"))
    # Múi giờ lưu thời gian (Việt Nam UTC+7, không có giờ mùa hè)
    UTC_OFFSET_HOURS = int(os.environ.get("UTC_OFFSET_HOURS", "7"))
    CSRF_ENABLED = True
