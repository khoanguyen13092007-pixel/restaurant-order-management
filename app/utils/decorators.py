"""NV1 - Phân quyền theo vai trò. Các module khác chỉ việc gắn decorator."""
from functools import wraps

from flask import abort, redirect, session, url_for


def login_required(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return inner


def role_required(*roles):
    """Ví dụ: @role_required("Manager") hoặc @role_required("Waitstaff", "Manager")."""
    def wrapper(fn):
        @wraps(fn)
        def inner(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))
            if session.get("role") not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return inner
    return wrapper
