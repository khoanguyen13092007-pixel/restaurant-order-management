"""NV3 - Customer self-ordering (FR-06), no login. Customers scan a QR code: /customer/<table code>."""
from flask import Blueprint, redirect, render_template, request, url_for

from app.controllers.order_controller import order_lines, render_menu_order
from app.services.errors import ServiceError
from app.services.order_service import OrderService
from app.services.table_service import TableService
from app.utils.web import attempt, claimed_order, remember_token

bp = Blueprint("customer", __name__, url_prefix="/customer")


def _known_table(code):
    try:
        TableService().get_by_code(code)
        return True
    except ServiceError:
        return False


@bp.route("/", defaults={"table_code": ""})
@bp.route("/<table_code>")
def order_page(table_code):
    if table_code and not _known_table(table_code):
        return render_template("error.html", code=404, message="Table not found."), 404
    return render_menu_order("customer", url_for("customer.place_order"), table_code)


@bp.route("/<table_code>/thanks")
def thanks(table_code):
    return render_template("customer/thanks.html", table_code=table_code,
                           order_id=request.args.get("order"))


@bp.post("/", defaults={"table_code": ""})
@bp.post("/<table_code>")
def place_order(table_code):
    f = request.form
    code = f.get("table_code") or table_code
    token = f.get("request_token")
    existing = claimed_order(token)
    if existing:  # form sent again: do not create a duplicate order
        return redirect(url_for("customer.thanks", table_code=code, order=existing))
    ok, order_id = attempt(lambda: OrderService().place_customer_order(
        code, order_lines(f), note=f.get("note")))
    if not ok:
        return render_menu_order("customer", url_for("customer.place_order"), code), 400
    remember_token(token, order_id)
    return redirect(url_for("customer.thanks", table_code=code, order=order_id))
