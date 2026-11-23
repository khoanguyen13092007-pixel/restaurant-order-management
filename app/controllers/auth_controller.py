"""NV1 - Login, logout and the role's home screen."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.auth_service import AuthError, AuthService
from app.utils.decorators import login_required

bp = Blueprint("auth", __name__)

# Each role starts on its own screen of the GUI design
HOME = {"Waitstaff": "tables.screen", "Kitchen": "kitchen.board",
        "Cashier": "payment.screen", "Manager": "menu.manage"}


@bp.route("/")
def index():
    return redirect(url_for("auth.dashboard") if "user_id" in session else url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            user = AuthService().authenticate(
                request.form.get("username"), request.form.get("password"))
        except AuthError as e:
            flash(str(e), "error")
            return render_template("auth/login.html", username=request.form.get("username", "")), 401
        session.clear()
        session.permanent = True  # session expires after a period of inactivity
        session["user_id"] = user.user_id
        session["role"] = user.role
        session["full_name"] = user.full_name
        return redirect(url_for("auth.dashboard"))
    return render_template("auth/login.html", username="")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


@bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for(HOME[session["role"]]))
