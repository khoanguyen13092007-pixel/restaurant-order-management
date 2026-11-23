"""NV4 - KitchenTicket (class diagram mục 5.2)."""


class KitchenTicket:
    def __init__(self, ticket_id, order_id, status="received", created_at=None):
        self.ticket_id = ticket_id
        self.order_id = order_id
        self.status = status
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        return cls(row["ticket_id"], row["order_id"], row["status"], row["created_at"])

    def send(self):
        """Gửi các món chưa có phiếu của đơn lên bếp; trả về mã phiếu."""
        if self.ticket_id is not None:
            return self.ticket_id
        from app.repositories.order_repository import OrderItemRepository
        from app.services.kitchen_service import KitchenService
        item_ids = OrderItemRepository().unsent_item_ids(self.order_id)
        self.ticket_id = KitchenService().create_ticket(self.order_id, item_ids)
        self.status = "received"
        return self.ticket_id

    def getItems(self):
        from app.services.kitchen_service import KitchenService
        return KitchenService().items_of_ticket(self.ticket_id)
