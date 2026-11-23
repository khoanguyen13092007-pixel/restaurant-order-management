"""NV3 - Customer, Order, OrderItem (class diagram mục 5.2)."""


class Customer:
    def __init__(self, customer_id, full_name, phone=None):
        self.customer_id = customer_id
        self.full_name = full_name
        self.phone = phone

    def viewMenu(self):
        from app.services.menu_service import MenuService
        return MenuService().search_items(only_available=True)

    def searchMenu(self, keyword):
        from app.services.menu_service import MenuService
        return MenuService().search_items(keyword, only_available=True)

    def placeOrder(self, table_code, lines):
        """lines = [{menu_item_id, quantity, note}]; trả về mã đơn."""
        from app.services.order_service import OrderService
        return OrderService().place_customer_order(
            table_code, lines, self.full_name, self.phone)


class Order:
    def __init__(self, order_id, status="draft", note=None, subtotal=0,
                 discount_amount=0, tax_amount=0, total_amount=0, created_at=None):
        self.order_id = order_id
        self.status = status
        self.note = note
        self.subtotal = subtotal
        self.discount_amount = discount_amount
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        return cls(row["order_id"], row["status"], row["note"], row["subtotal"],
                   row["discount_amount"], row["tax_amount"], row["total_amount"],
                   row["created_at"])

    def _refresh(self):
        from app.services.order_service import OrderService
        fresh = OrderService().get_order(self.order_id)["order"]
        self.__dict__.update(Order.from_row(fresh).__dict__)

    def addItem(self, menu_item_id, quantity, note=None):
        from app.services.order_service import OrderService
        item_id = OrderService().add_item(self.order_id, menu_item_id, quantity, note)
        self._refresh()
        return item_id

    def removeItem(self, order_item_id):
        from app.services.order_service import OrderService
        OrderService().cancel_item(order_item_id)
        self._refresh()

    def confirm(self, waitstaff_id=None):
        from app.services.order_service import OrderService
        ticket_id = OrderService().confirm_order(self.order_id, waitstaff_id)
        self._refresh()
        return ticket_id

    def cancel(self):
        from app.services.order_service import OrderService
        OrderService().cancel_order(self.order_id)
        self._refresh()

    def calculateTotal(self, discount_amount=0):
        from app.services import pricing
        totals = pricing.recalculate_order(self.order_id, discount_amount)
        self._refresh()
        return totals


class OrderItem:
    def __init__(self, order_item_id, order_id, menu_item_id, quantity,
                 unit_price, note=None, status="pending", ticket_id=None):
        self.order_item_id = order_item_id
        self.order_id = order_id
        self.menu_item_id = menu_item_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.note = note
        self.status = status
        self.ticket_id = ticket_id

    @classmethod
    def from_row(cls, row):
        return cls(row["order_item_id"], row["order_id"], row["menu_item_id"],
                   row["quantity"], row["unit_price"], row["note"], row["status"],
                   row["ticket_id"])

    def updateQuantity(self, quantity):
        from app.services.order_service import OrderService
        OrderService().update_quantity(self.order_item_id, quantity)
        self.quantity = int(quantity)

    def updateStatus(self, status):
        from app.services.kitchen_service import KitchenService
        KitchenService().update_item_status(self.order_item_id, status)
        self.status = status

    def cancel(self):
        from app.services.order_service import OrderService
        OrderService().cancel_item(self.order_item_id)
        self.status = "cancelled"

    def getSubtotal(self):
        return self.quantity * self.unit_price

    def canModify(self):
        """Chỉ sửa/huỷ được khi bếp chưa bắt đầu nấu."""
        return self.status == "pending"
