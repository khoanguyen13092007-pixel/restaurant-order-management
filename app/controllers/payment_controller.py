"""NV5 - Cashier screen, invoice and manager reports."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.services.errors import ServiceError
from app.services.order_service import OrderService
from app.services.payment_service import METHODS, PaymentService
from app.utils.decorators import role_required
from app.utils.web import attempt

bp = Blueprint("payment", __name__, url_prefix="/payment")


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@bp.route("/")
@role_required("Cashier")
def screen():
    """Cashier: choose a table, 'Find order', then see the Bill and confirm payment."""
    service = PaymentService()
    table_id, paid_order_id = _int(request.args.get("table")), _int(request.args.get("order"))
    discount = request.args.get("discount", "0")
    ctx = {"tables": service.payable_tables(), "table_id": table_id, "methods": METHODS,
           "order": None, "totals": None, "discount": discount, "paid": None}
    try:
        if paid_order_id:  # just paid: show the finished bill, 'Print invoice' becomes available
            data = OrderService().get_order(paid_order_id)
            payment = service.payment_of_order(paid_order_id)
            if payment is not None:
                ctx.update(order=data, paid=payment, totals={
                    "subtotal": data["order"]["subtotal"], "discount_amount": data["order"]["discount_amount"],
                    "tax_amount": data["order"]["tax_amount"], "total_amount": data["order"]["total_amount"]})
        elif table_id:
            order_id = service.order_for_table(table_id)
            ctx["order"] = OrderService().get_order(order_id)
            ctx["totals"] = service.preview(order_id, discount)
    except ServiceError as e:
        flash(str(e), "error")
    return render_template("payment/payment.html", **ctx)


@bp.post("/<int:order_id>/pay")
@role_required("Cashier")
def pay(order_id):
    f = request.form
    ok, result = attempt(lambda: PaymentService().process_payment(
        order_id, session["user_id"], f.get("method"), f.get("discount", 0), f.get("cash_received")),
        "Payment successful. The table is available again.")
    if not ok:
        return redirect(url_for("payment.screen", table=_int(f.get("table_id")), discount=f.get("discount", 0)))
    return redirect(url_for("payment.screen", order=order_id))


@bp.route("/invoice/<int:payment_id>")
@role_required("Cashier", "Manager")
def invoice(payment_id):
    ok, data = attempt(lambda: PaymentService().get_invoice(payment_id))
    if not ok:
        return redirect(url_for("payment.screen"))
    return render_template("payment/invoice.html", **data)


@bp.route("/reports")
@role_required("Manager")
def reports():
    service = PaymentService()
    period = request.args.get("period", "day")
    start, end = request.args.get("start", ""), request.args.get("end", "")
    try:
        revenue = service.revenue_report(period, start, end)
        best = service.best_selling(start, end, 10)
    except ServiceError as e:
        flash(str(e), "error")
        d_start, d_end = service.default_range()
        period = "day"
        revenue = service.revenue_report("day", d_start, d_end)
        best = service.best_selling(d_start, d_end, 10)
    return render_template("payment/reports.html", revenue=revenue, best=best, period=period)
