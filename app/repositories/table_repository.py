from app.database import get_db
from app.repositories.base_repository import BaseRepository

ACTIVE_SQL = "('draft','confirmed')"


class RestaurantTableRepository(BaseRepository):  # NV2
    table = "RESTAURANT_TABLE"
    pk = "table_id"

    def find_by_code(self, code):
        return get_db().execute(
            'SELECT * FROM "RESTAURANT_TABLE" WHERE code = ?', (code,)
        ).fetchone()

    def list_with_orders(self):
        return get_db().execute(
            f"""SELECT rt.*, MAX(o.order_id) AS active_order_id
                FROM "RESTAURANT_TABLE" rt
                LEFT JOIN "ORDER_TABLE" ot ON ot.table_id = rt.table_id
                LEFT JOIN "ORDER" o ON o.order_id = ot.order_id AND o.status IN {ACTIVE_SQL}
                GROUP BY rt.table_id ORDER BY rt.code"""
        ).fetchall()

    def has_history(self, table_id):
        return get_db().execute(
            'SELECT COUNT(*) FROM "ORDER_TABLE" WHERE table_id = ?', (table_id,)
        ).fetchone()[0] > 0


class OrderTableRepository:  # NV2 - bảng nối ORDER_TABLE (khoá chính ghép)
    def link(self, order_id, table_id):
        get_db().execute(
            'INSERT OR IGNORE INTO "ORDER_TABLE" (order_id, table_id) VALUES (?, ?)',
            (order_id, table_id))
        get_db().commit()

    def unlink(self, order_id, table_id):
        get_db().execute(
            'DELETE FROM "ORDER_TABLE" WHERE order_id = ? AND table_id = ?',
            (order_id, table_id))
        get_db().commit()

    def tables_of_order(self, order_id):
        return get_db().execute(
            """SELECT rt.* FROM "ORDER_TABLE" ot
               JOIN "RESTAURANT_TABLE" rt ON rt.table_id = ot.table_id
               WHERE ot.order_id = ? ORDER BY rt.code""", (order_id,)
        ).fetchall()

    def active_order_of_table(self, table_id):
        return get_db().execute(
            f"""SELECT o.* FROM "ORDER_TABLE" ot JOIN "ORDER" o ON o.order_id = ot.order_id
                WHERE ot.table_id = ? AND o.status IN {ACTIVE_SQL} LIMIT 1""", (table_id,)
        ).fetchone()

    def relink_all(self, from_order, to_order):
        """Chuyển mọi bàn của đơn from_order sang to_order (dùng khi gộp đơn)."""
        db = get_db()
        db.execute(
            'INSERT OR IGNORE INTO "ORDER_TABLE" (order_id, table_id) '
            'SELECT ?, table_id FROM "ORDER_TABLE" WHERE order_id = ?', (to_order, from_order))
        db.execute('DELETE FROM "ORDER_TABLE" WHERE order_id = ?', (from_order,))
        db.commit()
        
