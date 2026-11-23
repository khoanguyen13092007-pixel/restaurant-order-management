"""Hàm tiện ích cho tầng giao diện: CSRF, định dạng tiền, nhãn tiếng Việt, bắt lỗi nghiệp vụ."""
import secrets

from flask import flash, session
from markupsafe import Markup

from app.services.errors import ServiceError

LABELS = {
    # order
    "draft": "Draft", "confirmed": "Confirmed", "paid": "Paid",
    "cancelled": "Cancelled", "merged": "Merged",
    # order item (names follow the GUI design)
    "pending": "Received", "preparing": "Cooking", "ready": "Done", "served": "Served",
    # table
    "available": "Available", "occupied": "Occupied",
    # kitchen ticket
    "received": "Received", "done": "Done",
    # payment
    "cash": "Cash", "card": "Card", "transfer": "Bank transfer",
}


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def csrf_field():
    return Markup('<input type="hidden" name="_csrf" value="%s">' % csrf_token())


def money(value):
    return "{:,.0f}".format(float(value or 0))


def vi_label(value):
    return LABELS.get(value, value)


def attempt(fn, success=None):
    """Chạy một thao tác nghiệp vụ; lỗi ServiceError được đưa ra bằng flash.
    Trả về (thành_công, kết_quả)."""
    try:
        result = fn()
    except ServiceError as e:
        flash(str(e), "error")
        return False, None
    if success:
        flash(success, "success")
    return True, result


def remember_token(token, order_id):
    tokens = dict(session.get("order_tokens", {}))
    tokens[token] = order_id
    session["order_tokens"] = dict(list(tokens.items())[-20:])


def claimed_order(token):
    return session.get("order_tokens", {}).get(token) if token else None
