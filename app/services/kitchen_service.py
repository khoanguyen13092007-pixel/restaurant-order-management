"""NV4 - Kitchen business logic: tickets, item status, ready notifications (FR-08, 09, 10)."""
from app.repositories.kitchen_repository import KitchenTicketRepository
from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.services.errors import ServiceError
from app.utils.timeutil import now_str

# Valid status flow of one dish
NEXT_STATUS = {"pending": "preparing", "preparing": "ready", "ready": "served"}
KITCHEN_TARGETS = ("preparing", "ready")   # the kitchen may only set these statuses


class KitchenService:
    def __init__(self):
        self.tickets = KitchenTicketRepository()
        self.items = OrderItemRepository()
        self.orders = OrderRepository()

    def create_ticket(self, order_id, item_ids):
        """Send dishes to the kitchen: create a ticket and attach it to each dish."""
        if not item_ids:
            raise ServiceError("There are no dishes to send to the kitchen.")
        ticket_id = self.tickets.add(
            {"order_id": order_id, "status": "received", "created_at": now_str()})
        for item_id in item_ids:
            self.items.update(item_id, {"ticket_id": ticket_id})
        return ticket_id

    def items_to_prepare(self):
        return self.tickets.items_with_status(("pending", "preparing"))

    def board(self, status=None):
        """Kitchen screen: dishes that are Received, Cooking or Done (optionally one status)."""
        wanted = ("pending", "preparing", "ready")
        if status in wanted:
            wanted = (status,)
        return self.tickets.items_with_status(wanted)

    def items_of_ticket(self, ticket_id):
        return self.tickets.items_of_ticket(ticket_id)

    def ready_items(self):
        """FR-10: dishes the kitchen has finished, waiting to be served."""
        return self.tickets.items_with_status(("ready",))

    def update_item_status(self, order_item_id, new_status):
        item = self._item(order_item_id)
        if new_status not in KITCHEN_TARGETS:
            raise ServiceError("Invalid status.")
        self._check_order_confirmed(item)
        if NEXT_STATUS.get(item["status"]) != new_status:
            raise ServiceError("This dish cannot move to that status.")
        self.items.update(order_item_id, {"status": new_status})
        self.sync_ticket(item["ticket_id"])

    def mark_served(self, order_item_id):
        item = self._item(order_item_id)
        self._check_order_confirmed(item)
        if item["status"] != "ready":
            raise ServiceError("Only a finished dish can be marked as served.")
        self.items.update(order_item_id, {"status": "served"})
        self.sync_ticket(item["ticket_id"])

    def sync_ticket(self, ticket_id):
        """Keep the kitchen ticket status in line with its dishes."""
        if ticket_id is None:
            return
        statuses = [i["status"] for i in self.tickets.items_of_ticket(ticket_id)
                    if i["status"] != "cancelled"]
        if not statuses:
            new = "cancelled"
        elif all(s in ("ready", "served") for s in statuses):
            new = "done"
        elif any(s in ("preparing", "ready", "served") for s in statuses):
            new = "preparing"
        else:
            new = "received"
        self.tickets.update(ticket_id, {"status": new})

    def _item(self, order_item_id):
        item = self.items.get_by_id(order_item_id)
        if item is None:
            raise ServiceError("Dish not found in the order.")
        return item

    def _check_order_confirmed(self, item):
        order = self.orders.get_by_id(item["order_id"])
        if order["status"] != "confirmed" or item["ticket_id"] is None:
            raise ServiceError("The order has not been sent to the kitchen or is already finished.")
