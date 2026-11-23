"""NV3 - Order business logic (FR-05, 06, 07)."""
from app.repositories.menu_repository import MenuItemRepository
from app.repositories.order_repository import (CustomerRepository, OrderItemRepository,
                                               OrderRepository)
from app.services import pricing
from app.services.errors import ServiceError
from app.services.kitchen_service import KitchenService
from app.services.table_service import TableService
from app.utils.timeutil import now_str

ACTIVE = ("draft", "confirmed")
MAX_QTY = 50


def parse_quantity(value):
    try:
        qty = int(value)
    except (TypeError, ValueError):
        raise ServiceError("Quantity is not a valid number.")
    if not 1 <= qty <= MAX_QTY:
        raise ServiceError(f"Quantity must be between 1 and {MAX_QTY}.")
    return qty


def _clean_note(note):
    return (note or "").strip()[:200] or None


class OrderService:
    def __init__(self):
        self.orders = OrderRepository()
        self.items = OrderItemRepository()
        self.menu = MenuItemRepository()
        self.customers = CustomerRepository()
        self.tables = TableService()
        self.kitchen = KitchenService()

    # ----- create orders -----
    def create_order(self, waitstaff_id=None, table_id=None, note=None, customer_id=None):
        if table_id:
            table = self.tables.get_table(table_id)
            if table["status"] != "available":
                raise ServiceError(f"Table {table['code']} is in use.")
        order_id = self.orders.add({
            "customer_id": customer_id, "waitstaff_id": waitstaff_id, "status": "draft",
            "note": _clean_note(note), "created_at": now_str(),
        })
        if table_id:
            self.tables.assign_table(order_id, table_id)
        return order_id

    def place_order_at_table(self, table_code, lines, customer_name=None, phone=None,
                             note=None, waitstaff_id=None, confirm=False):
        """Shared by the customer (FR-06) and the waitstaff (FR-05) on the Menu and Orders screen.
        lines = [{menu_item_id, quantity, note}]. If the table already has an open order the
        dishes are added to it. confirm=True also sends the new dishes to the kitchen."""
        table = self.tables.get_by_code(table_code)
        clean = []
        for line in lines:
            raw = str(line.get("quantity") or "").strip()
            if raw in ("", "0"):
                continue
            qty = parse_quantity(raw)
            self._available_menu_item(line.get("menu_item_id"))
            clean.append((int(line["menu_item_id"]), qty, line.get("note") or note))
        if not clean:
            raise ServiceError("Please choose at least one dish.")

        active = self.tables.active_order_for_table(table["table_id"])
        if active is not None:
            order_id = active["order_id"]
            if _clean_note(note):
                joined = "; ".join(x for x in (active["note"], _clean_note(note)) if x)
                self.orders.update(order_id, {"note": joined[:200]})
        else:
            customer_id = None
            if (customer_name or "").strip():
                customer_id = self.customers.add({
                    "full_name": customer_name.strip()[:100],
                    "phone": (phone or "").strip()[:20] or None})
            order_id = self.create_order(waitstaff_id=waitstaff_id, table_id=table["table_id"],
                                         note=note, customer_id=customer_id)
        for menu_item_id, qty, item_note in clean:
            self.add_item(order_id, menu_item_id, qty, item_note)
        if confirm:
            self.confirm_order(order_id, waitstaff_id)
        return order_id

    def place_customer_order(self, table_code, lines, customer_name=None, phone=None, note=None):
        """FR-06: the customer orders at the table; the order waits for the waitstaff to confirm."""
        return self.place_order_at_table(table_code, lines, customer_name, phone, note)

    # ----- dishes in an order -----
    def _active_order(self, order_id):
        order = self.orders.get_by_id(order_id) if order_id else None
        if order is None:
            raise ServiceError("Order not found.")
        if order["status"] not in ACTIVE:
            raise ServiceError("This order is finished and cannot be changed.")
        return order

    def _available_menu_item(self, menu_item_id):
        try:
            row = self.menu.get_by_id(int(menu_item_id))
        except (TypeError, ValueError):
            row = None
        if row is None:
            raise ServiceError("This dish does not exist.")
        if not row["is_available"]:
            raise ServiceError(f"'{row['name']}' is sold out.")
        return row

    def add_item(self, order_id, menu_item_id, quantity, note=None):
        self._active_order(order_id)
        qty = parse_quantity(quantity)
        menu_item = self._available_menu_item(menu_item_id)
        item_id = self.items.add({
            "order_id": order_id, "menu_item_id": menu_item["menu_item_id"],
            "quantity": qty, "unit_price": menu_item["price"],
            "note": _clean_note(note), "status": "pending",
        })
        pricing.recalculate_order(order_id)
        return item_id

    def _modifiable_item(self, order_item_id):
        item = self.items.get_by_id(order_item_id)
        if item is None:
            raise ServiceError("Dish not found in the order.")
        self._active_order(item["order_id"])
        if item["status"] != "pending":
            raise ServiceError("The kitchen has started this dish, it can no longer be edited or cancelled.")
        return item

    def update_quantity(self, order_item_id, quantity):
        item = self._modifiable_item(order_item_id)
        self.items.update(order_item_id, {"quantity": parse_quantity(quantity)})
        pricing.recalculate_order(item["order_id"])

    def cancel_item(self, order_item_id):
        item = self._modifiable_item(order_item_id)
        self.items.update(order_item_id, {"status": "cancelled"})
        self.kitchen.sync_ticket(item["ticket_id"])
        pricing.recalculate_order(item["order_id"])

    # ----- confirm / cancel an order -----
    def confirm_order(self, order_id, waitstaff_id=None):
        """Confirm the order and send the new dishes to the kitchen. Returns the ticket id."""
        order = self._active_order(order_id)
        unsent = self.items.unsent_item_ids(order_id)
        if not unsent:
            if order["status"] == "draft":
                raise ServiceError("The order has no dishes to confirm.")
            raise ServiceError("There are no new dishes to send (the order is already confirmed).")
        ticket_id = self.kitchen.create_ticket(order_id, unsent)
        changes = {"status": "confirmed"}
        if waitstaff_id and order["waitstaff_id"] is None:
            changes["waitstaff_id"] = waitstaff_id
        self.orders.update(order_id, changes)
        pricing.recalculate_order(order_id)
        return ticket_id

    def cancel_order(self, order_id):
        self._active_order(order_id)
        if self.items.count_with_status(order_id, ("preparing", "ready", "served")):
            raise ServiceError("The kitchen has started cooking, the whole order cannot be cancelled.")
        tickets = {i["ticket_id"] for i in self.items.items_of_order(order_id)
                   if i["ticket_id"] is not None}
        self.items.cancel_all_pending(order_id)
        self.orders.update(order_id, {"status": "cancelled"})
        for ticket_id in tickets:
            self.kitchen.sync_ticket(ticket_id)
        pricing.recalculate_order(order_id)
        self.tables.release_tables(order_id)

    # ----- queries -----
    def get_order(self, order_id):
        order = self.orders.get_by_id(order_id) if order_id else None
        if order is None:
            raise ServiceError("Order not found.")
        items = [dict(i, can_modify=(i["status"] == "pending" and order["status"] in ACTIVE))
                 for i in self.items.items_of_order(order_id)]
        return {"order": order, "items": items,
                "tables": self.tables.tables_of_order(order_id),
                "unsent": len(self.items.unsent_item_ids(order_id))}

    def list_orders(self, statuses=None):
        return self.orders.list_by_status(statuses)
