""NV2 - Table business logic: status, assign, move, merge tables (FR-03, FR-04)."""
from app.repositories.order_repository import OrderRepository
from app.repositories.table_repository import OrderTableRepository, RestaurantTableRepository
from app.services import pricing
from app.services.errors import ServiceError

ACTIVE = ("draft", "confirmed")


def _clean_code(code):
    code = (code or "").strip()
    if not code:
        raise ServiceError("The table code cannot be empty.")
    if len(code) > 20:
        raise ServiceError("The table code is too long (maximum 20 characters).")
    if "/" in code or " " in code:
        raise ServiceError("The table code cannot contain spaces or '/'.")
    return code


class TableService:
    def __init__(self):
        self.tables = RestaurantTableRepository()
        self.links = OrderTableRepository()
        self.orders = OrderRepository()

    # ----- view / manage tables -----
    def list_tables(self):
        return self.tables.list_with_orders()

    def get_table(self, table_id):
        row = self.tables.get_by_id(table_id) if table_id else None
        if row is None:
            raise ServiceError("Table not found.")
        return row

    def get_by_code(self, code):
        row = self.tables.find_by_code((code or "").strip())
        if row is None:
            raise ServiceError("Table not found.")
        return row

    def available_tables(self):
        return [t for t in self.tables.get_all() if t["status"] == "available"]

    def create_table(self, code):
        code = _clean_code(code)
        if self.tables.find_by_code(code):
            raise ServiceError("This table code already exists.")
        return self.tables.add({"code": code})

    def rename_table(self, table_id, code):
        self.get_table(table_id)
        code = _clean_code(code)
        other = self.tables.find_by_code(code)
        if other and other["table_id"] != table_id:
            raise ServiceError("This table code already exists.")
        self.tables.update(table_id, {"code": code})

    def delete_table(self, table_id):
        table = self.get_table(table_id)
        if table["status"] != "available" or self.tables.has_history(table_id):
            raise ServiceError("A table that is occupied or has had orders cannot be deleted.")
        self.tables.delete(table_id)

    def set_status(self, table_id, status):
        self.get_table(table_id)
        self.tables.update(table_id, {"status": status})

    def active_order_for_table(self, table_id):
        return self.links.active_order_of_table(table_id)

    def tables_of_order(self, order_id):
        return self.links.tables_of_order(order_id)

    # ----- assign / move / merge -----
    def _active_order(self, order_id):
        order = self.orders.get_by_id(order_id) if order_id else None
        if order is None:
            raise ServiceError("Order not found.")
        if order["status"] not in ACTIVE:
            raise ServiceError("This order is finished, its tables cannot be changed.")
        return order

    def assign_table(self, order_id, table_id):
        self._active_order(order_id)
        table = self.get_table(table_id)
        if table["status"] != "available":
            raise ServiceError(f"Table {table['code']} is in use.")
        self.links.link(order_id, table_id)
        self.set_status(table_id, "occupied")

    def move_table(self, order_id, from_table_id, to_table_id):
        self._active_order(order_id)
        if from_table_id == to_table_id:
            raise ServiceError("The source and target tables must be different.")
        current = {t["table_id"] for t in self.links.tables_of_order(order_id)}
        if from_table_id not in current:
            raise ServiceError("The source table does not belong to this order.")
        target = self.get_table(to_table_id)
        if target["status"] != "available":
            raise ServiceError(f"Table {target['code']} is in use.")
        self.links.unlink(order_id, from_table_id)
        self.set_status(from_table_id, "available")
        self.links.link(order_id, to_table_id)
        self.set_status(to_table_id, "occupied")

    def merge_tables(self, order_id, table_ids):
        """Add more tables to the order. A free table is assigned to it; a table with another
        order merges that order (items, kitchen tickets, tables) into this one."""
        order = self._active_order(order_id)
        ids = []
        for tid in table_ids:
            tid = int(tid)
            if tid not in ids:
                ids.append(tid)
        if not ids:
            raise ServiceError("Select at least one table to merge.")

        plans = []
        for tid in ids:
            table = self.get_table(tid)
            other = self.links.active_order_of_table(tid)
            if other is not None and other["order_id"] == order_id:
                raise ServiceError(f"Table {table['code']} already belongs to this order.")
            if other is None and table["status"] != "available":
                raise ServiceError(f"Table {table['code']} is in use.")
            plans.append((tid, other))

        merged_sources = set()
        for tid, other in plans:
            if other is None:
                self.links.link(order_id, tid)
                self.set_status(tid, "occupied")
            elif other["order_id"] not in merged_sources:
                self._merge_orders(source=other, target=order)
                merged_sources.add(other["order_id"])
        return len(ids)

    def _merge_orders(self, source, target):
        src_id, tgt_id = source["order_id"], target["order_id"]
        self.orders.move_items_and_tickets(src_id, tgt_id)
        self.links.relink_all(src_id, tgt_id)
        self.orders.update(src_id, {"status": "merged", "note": f"Merged into order #{tgt_id}"})
        if source["status"] == "confirmed" and target["status"] == "draft":
            self.orders.update(tgt_id, {"status": "confirmed"})
        pricing.recalculate_order(src_id)
        pricing.recalculate_order(tgt_id)

    def release_tables(self, order_id):
        for table in self.links.tables_of_order(order_id):
            self.set_status(table["table_id"], "available")
