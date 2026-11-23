"""NV5 - Payment, invoice, reports (FR-11, 12, 13)."""
from datetime import date, timedelta

from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.repositories.payment_repository import PERIOD_FORMATS, PaymentRepository
from app.repositories.user_repository import UserRepository
from app.services import pricing
from app.services.errors import ServiceError
from app.services.table_service import TableService
from app.utils.timeutil import now_str, today_str

METHODS = ("cash", "card", "transfer")


def _parse_date(value, label):
    try:
        return date.fromisoformat((value or "").strip()).isoformat()
    except ValueError:
        raise ServiceError(f"{label} is not a valid date (use YYYY-MM-DD).")


class PaymentService:
    def __init__(self):
        self.payments = PaymentRepository()
        self.orders = OrderRepository()
        self.items = OrderItemRepository()
        self.users = UserRepository()
        self.tables = TableService()

    # ----- find the order to pay -----
    def payable_tables(self):
        """Tables that currently have an open order (for the 'Table' list on the cashier screen)."""
        return [t for t in self.tables.list_tables() if t["active_order_id"]]

    def order_for_table(self, table_id):
        table = self.tables.get_table(table_id)
        order = self.tables.active_order_for_table(table_id)
        if order is None:
            raise ServiceError(f"Table {table['code']} has no open order.")
        if order["status"] != "confirmed":
            raise ServiceError(f"Order #{order['order_id']} has not been confirmed yet.")
        return order["order_id"]

    def _payable_order(self, order_id):
        order = self.orders.get_by_id(order_id) if order_id else None
        if order is None:
            raise ServiceError("Order not found.")
        if order["status"] == "paid":
            raise ServiceError("This order has already been paid.")
        if order["status"] != "confirmed":
            raise ServiceError("Only a confirmed order can be paid.")
        if self.items.unsent_item_ids(order_id):
            raise ServiceError("The order has dishes not sent to the kitchen. Confirm the order before payment.")
        if self.items.subtotal_of_order(order_id) <= 0:
            raise ServiceError("The order has nothing to pay.")
        return order

    # ----- totals -----
    def preview(self, order_id, discount_amount=0):
        """FR-11: subtotal, discount, tax and total (not saved)."""
        self._payable_order(order_id)
        subtotal = self.items.subtotal_of_order(order_id)
        discount = pricing.parse_discount_amount(discount_amount, subtotal)
        return pricing.compute_totals(subtotal, discount)

    def list_payable_orders(self):
        return self.orders.list_by_status(("confirmed",))

    # ----- payment -----
    def process_payment(self, order_id, cashier_id, method, discount_amount=0, cash_received=None):
        self._payable_order(order_id)
        if self.payments.find_paid_for_order(order_id):
            raise ServiceError("This order has already been paid.")
        if method not in METHODS:
            raise ServiceError("Please choose a payment method.")
        subtotal = self.items.subtotal_of_order(order_id)
        discount = pricing.parse_discount_amount(discount_amount, subtotal)
        totals = pricing.compute_totals(subtotal, discount)

        change = None
        if method == "cash" and str(cash_received or "").strip() != "":
            try:
                received = float(cash_received)
            except ValueError:
                raise ServiceError("The cash received is not a valid number.")
            if received < totals["total_amount"]:
                raise ServiceError("The cash received is not enough.")
            change = received - totals["total_amount"]

        payment_id = self.payments.add({
            "order_id": order_id, "cashier_id": cashier_id,
            "amount": totals["total_amount"], "method": method,
            "status": "paid", "paid_at": now_str(),
        })
        self.orders.update(order_id, {**totals, "status": "paid"})
        self.tables.release_tables(order_id)
        return {"payment_id": payment_id, "total": totals["total_amount"], "change": change}

    def payment_of_order(self, order_id):
        return self.payments.find_paid_for_order(order_id)

    def get_invoice(self, payment_id):
        payment = self.payments.get_by_id(payment_id)
        if payment is None:
            raise ServiceError("Invoice not found.")
        order = self.orders.get_by_id(payment["order_id"])
        cashier = self.users.get_by_id(payment["cashier_id"])
        items = [i for i in self.items.items_of_order(order["order_id"]) if i["status"] != "cancelled"]
        return {"payment": payment, "order": order, "items": items,
                "tables": self.tables.tables_of_order(order["order_id"]),
                "cashier_name": cashier["full_name"] if cashier else ""}

    # ----- reports (FR-13) -----
    @staticmethod
    def default_range():
        today = date.fromisoformat(today_str())
        return (today - timedelta(days=29)).isoformat(), today.isoformat()

    def _range(self, start, end):
        default_start, default_end = self.default_range()
        start = _parse_date(start, "The start date") if start else default_start
        end = _parse_date(end, "The end date") if end else default_end
        if start > end:
            raise ServiceError("The start date must be on or before the end date.")
        return start, end

    def revenue_report(self, period="day", start=None, end=None):
        if period not in PERIOD_FORMATS:
            raise ServiceError("Invalid report period (use day, week or month).")
        start, end = self._range(start, end)
        rows = self.payments.revenue_by_period(period, start, end)
        return {"period": period, "start": start, "end": end, "rows": rows,
                "total_revenue": sum(r["revenue"] for r in rows),
                "total_payments": sum(r["payments"] for r in rows)}

    def best_selling(self, start=None, end=None, limit=10):
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            raise ServiceError("The number of dishes is not valid.")
        if not 1 <= limit <= 100:
            raise ServiceError("The number of dishes must be between 1 and 100.")
        start, end = self._range(start, end)
        return self.payments.best_selling(start, end, limit)
