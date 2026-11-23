"""NV3 - Waitstaff order routes: the Menu and Orders screen and order actions."""
import uuid

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.menu_service import MenuService
from app.services.order_service import OrderService
from app.services.table_service import TableService
from app.utils.decorators import role_required
from app.utils.web import attempt, claimed_order, remember_token

bp = Blueprint("orders", __name__, url_prefix="/orders")
STAFF = ("Waitstaff", "Manager")


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_screen(order_id):
    return redirect(url_for("tables.screen", order=order_id))


def order_lines(form):
    """Read the cart from the form: qty_<menu item id> fields."""
    return [{"menu_item_id": key[4:], "quantity": value} for key, value in form.items()
            if key.startswith("qty_")]


def render_menu_order(mode, action, table_code=""):
    service = MenuService()
    return render_template("orders/menu_order.html", mode=mode, action=action,
                           items=service.search_items(), categories=service.list_categories(),
                           tables=TableService().list_tables(), selected_code=table_code,
                           request_token=uuid.uuid4().hex)


@bp.route("/")
@role_required(*STAFF)
def list_orders():
    return redirect(url_for("tables.screen"))


@bp.route("/new", methods=["GET", "POST"])
@role_required("Waitstaff")
def new():
    """Menu and Orders (waitstaff): 'Confirm order & send to kitchen' creates and confirms the order."""
    if request.method == "POST":
        f = request.form
        token = f.get("request_token")
        existing = claimed_order(token)
        if existing:  # form sent again (double click, reload): do not create a duplicate order
            flash("This order was already created.", "success")
            return _to_screen(existing)
        ok, order_id = attempt(lambda: OrderService().place_order_at_table(
            f.get("table_code"), order_lines(f), note=f.get("note"),
            waitstaff_id=session["user_id"], confirm=True), "Order confirmed and sent to the kitchen.")
        if ok:
            remember_token(token, order_id)
            return _to_screen(order_id)
        return render_menu_order("staff", url_for("orders.new"), f.get("table_code", "")), 400
    return render_menu_order("staff", url_for("orders.new"), request.args.get("table", ""))


@bp.route("/<int:order_id>")
@role_required(*STAFF)
def detail(order_id):
    return _to_screen(order_id)


@bp.post("/<int:order_id>/items")
@role_required(*STAFF)
def add_item(order_id):
    f = request.form
    attempt(lambda: OrderService().add_item(
        order_id, f.get("menu_item_id"), f.get("quantity"), f.get("note")), "Dish added.")
    return _to_screen(order_id)


@bp.post("/items/<int:item_id>/quantity")
@role_required(*STAFF)
def item_quantity(item_id):
    attempt(lambda: OrderService().update_quantity(item_id, request.form.get("quantity")),
            "Quantity updated.")
    return _to_screen(_int(request.form.get("order_id")))


@bp.post("/items/<int:item_id>/cancel")
@role_required(*STAFF)
def item_cancel(item_id):
    attempt(lambda: OrderService().cancel_item(item_id), "Dish cancelled.")
    return _to_screen(_int(request.form.get("order_id")))


@bp.post("/<int:order_id>/confirm")
@role_required(*STAFF)
def confirm(order_id):
    attempt(lambda: OrderService().confirm_order(order_id, session["user_id"]),
            "Order confirmed and sent to the kitchen.")
    return _to_screen(order_id)


@bp.post("/<int:order_id>/cancel")
@role_required(*STAFF)
def cancel(order_id):
    ok, _ = attempt(lambda: OrderService().cancel_order(order_id), "Order cancelled.")
    return _to_screen(None if ok else order_id)
