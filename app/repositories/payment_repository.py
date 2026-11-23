from app.database import get_db
from app.repositories.base_repository import BaseRepository

PERIOD_FORMATS = {"day": "%Y-%m-%d", "week": "%Y-W%W", "month": "%Y-%m"}


class PaymentRepository(BaseRepository):  # NV5
    table = "PAYMENT"
    pk = "payment_id"

    def find_paid_for_order(self, order_id):
        return get_db().execute(
            'SELECT * FROM "PAYMENT" WHERE order_id = ? AND status = \'paid\'', (order_id,)
        ).fetchone()

    def revenue_by_period(self, period, start, end):
        fmt = PERIOD_FORMATS[period]
        return get_db().execute(
            """SELECT strftime(?, paid_at) AS period, COUNT(*) AS payments, SUM(amount) AS revenue
               FROM "PAYMENT" WHERE status = 'paid' AND date(paid_at) BETWEEN ? AND ?
               GROUP BY period ORDER BY period""", (fmt, start, end)
        ).fetchall()

    def best_selling(self, start, end, limit):
        return get_db().execute(
            """SELECT mi.menu_item_id, mi.name, SUM(oi.quantity) AS quantity,
                      SUM(oi.quantity * oi.unit_price) AS revenue
               FROM "PAYMENT" p
               JOIN "ORDER_ITEM" oi ON oi.order_id = p.order_id AND oi.status != 'cancelled'
               JOIN "MENU_ITEM" mi ON mi.menu_item_id = oi.menu_item_id
               WHERE p.status = 'paid' AND date(p.paid_at) BETWEEN ? AND ?
               GROUP BY mi.menu_item_id ORDER BY quantity DESC, revenue DESC, mi.name LIMIT ?""",
            (start, end, limit)
        ).fetchall()
