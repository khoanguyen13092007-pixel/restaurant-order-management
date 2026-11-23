from app.database import get_db
from app.repositories.base_repository import BaseRepository

_ITEM_COLUMNS = """
    oi.order_item_id, oi.order_id, oi.ticket_id, oi.quantity, oi.note, oi.status,
    mi.name AS item_name, kt.created_at AS ticket_created,
    (SELECT group_concat(rt.code, ', ') FROM "ORDER_TABLE" ot
       JOIN "RESTAURANT_TABLE" rt ON rt.table_id = ot.table_id
       WHERE ot.order_id = oi.order_id) AS table_codes
"""
_ITEM_JOINS = """
    FROM "ORDER_ITEM" oi
    JOIN "ORDER" o ON o.order_id = oi.order_id
    JOIN "MENU_ITEM" mi ON mi.menu_item_id = oi.menu_item_id
    JOIN "KITCHEN_TICKET" kt ON kt.ticket_id = oi.ticket_id
"""


class KitchenTicketRepository(BaseRepository):  # NV4
    table = "KITCHEN_TICKET"
    pk = "ticket_id"

    def items_with_status(self, statuses):
        marks = ",".join("?" for _ in statuses)
        return get_db().execute(
            f"""SELECT {_ITEM_COLUMNS} {_ITEM_JOINS}
                WHERE o.status = 'confirmed' AND oi.status IN ({marks})
                ORDER BY kt.created_at, oi.order_item_id""", tuple(statuses)
        ).fetchall()

    def items_of_ticket(self, ticket_id):
        return get_db().execute(
            """SELECT oi.*, mi.name AS item_name FROM "ORDER_ITEM" oi
               JOIN "MENU_ITEM" mi ON mi.menu_item_id = oi.menu_item_id
               WHERE oi.ticket_id = ? ORDER BY oi.order_item_id""", (ticket_id,)
        ).fetchall()
