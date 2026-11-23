from app.database import get_db
from app.repositories.base_repository import BaseRepository


class CustomerRepository(BaseRepository):  # NV3
    table = "CUSTOMER"
    pk = "customer_id"


class OrderRepository(BaseRepository):  # NV3
    table = "ORDER"
    pk = "order_id"

    def list_by_status(self, statuses=None):
        sql = """SELECT o.*,
                   (SELECT group_concat(rt.code, ', ') FROM "ORDER_TABLE" ot
                      JOIN "RESTAURANT_TABLE" rt ON rt.table_id = ot.table_id
                      WHERE ot.order_id = o.order_id) AS table_codes,
                   (SELECT COUNT(*) FROM "ORDER_ITEM" oi
                      WHERE oi.order_id = o.order_id AND oi.status = 'pending'
                        AND oi.ticket_id IS NULL) AS unsent_items
                 FROM "ORDER" o"""
        params = ()
        if statuses:
            sql += " WHERE o.status IN (%s)" % ",".join("?" for _ in statuses)
            params = tuple(statuses)
        sql += " ORDER BY o.order_id DESC"
        return get_db().execute(sql, params).fetchall()

    def move_items_and_tickets(self, from_order, to_order):
        db = get_db()
        db.execute('UPDATE "ORDER_ITEM" SET order_id = ? WHERE order_id = ?', (to_order, from_order))
        db.execute('UPDATE "KITCHEN_TICKET" SET order_id = ? WHERE order_id = ?', (to_order, from_order))
        db.commit()


class OrderItemRepository(BaseRepository):  # NV3
    table = "ORDER_ITEM"
    pk = "order_item_id"

    def items_of_order(self, order_id):
        return get_db().execute(
            """SELECT oi.*, mi.name AS item_name FROM "ORDER_ITEM" oi
               JOIN "MENU_ITEM" mi ON mi.menu_item_id = oi.menu_item_id
               WHERE oi.order_id = ? ORDER BY oi.order_item_id""", (order_id,)
        ).fetchall()

    def subtotal_of_order(self, order_id):
        return get_db().execute(
            """SELECT COALESCE(SUM(quantity * unit_price), 0) FROM "ORDER_ITEM"
               WHERE order_id = ? AND status != 'cancelled'""", (order_id,)
        ).fetchone()[0]

    def unsent_item_ids(self, order_id):
        rows = get_db().execute(
            """SELECT order_item_id FROM "ORDER_ITEM"
               WHERE order_id = ? AND status = 'pending' AND ticket_id IS NULL
               ORDER BY order_item_id""", (order_id,)
        ).fetchall()
        return [r[0] for r in rows]

    def count_with_status(self, order_id, statuses):
        marks = ",".join("?" for _ in statuses)
        return get_db().execute(
            f'SELECT COUNT(*) FROM "ORDER_ITEM" WHERE order_id = ? AND status IN ({marks})',
            (order_id, *statuses)
        ).fetchone()[0]

    def cancel_all_pending(self, order_id):
        get_db().execute(
            """UPDATE "ORDER_ITEM" SET status = 'cancelled'
               WHERE order_id = ? AND status = 'pending'""", (order_id,))
        get_db().commit()
