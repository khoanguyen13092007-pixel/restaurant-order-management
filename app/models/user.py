"""NV1 - User và 4 lớp con theo class diagram (mục 5.2)."""
from abc import ABC

from werkzeug.security import check_password_hash


class User(ABC):
    role = None  # được lớp con ghi đè

    def __init__(self, user_id, username, password_hash, full_name, status="active"):
        self.user_id = user_id
        self.username = username
        self.password_hash = password_hash
        self.full_name = full_name
        self.status = status

    @property
    def is_active(self):
        return self.status == "active"

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def login(self, password):
        """Trả về True nếu tài khoản đang hoạt động và mật khẩu đúng."""
        return self.is_active and self.check_password(password)

    def logout(self):
        """Việc xoá phiên do controller thực hiện; lớp chỉ đại diện nghiệp vụ."""
        return True


class Kitchen(User):
    role = "Kitchen"

    def viewItemsToPrepare(self):
        from app.services.kitchen_service import KitchenService
        return KitchenService().items_to_prepare()

    def updateItemStatus(self, order_item_id, status):
        from app.services.kitchen_service import KitchenService
        KitchenService().update_item_status(order_item_id, status)


class Waitstaff(User):
    role = "Waitstaff"

    def createOrder(self, table_id=None, note=None):
        from app.models.order import Order
        from app.services.order_service import OrderService
        service = OrderService()
        order_id = service.create_order(self.user_id, table_id, note)
        return Order.from_row(service.get_order(order_id)["order"])

    def editOrCancelItem(self, order_item_id, quantity=None):
        """Có quantity: sửa số lượng; không có: huỷ món (chỉ khi bếp chưa nấu)."""
        from app.services.order_service import OrderService
        service = OrderService()
        if quantity is None:
            service.cancel_item(order_item_id)
        else:
            service.update_quantity(order_item_id, quantity)

    def assignTable(self, order_id, table_id):
        from app.services.table_service import TableService
        TableService().assign_table(order_id, table_id)

    def moveTable(self, order_id, from_table_id, to_table_id):
        from app.services.table_service import TableService
        TableService().move_table(order_id, from_table_id, to_table_id)

    def mergeTables(self, order_id, table_ids):
        from app.services.table_service import TableService
        return TableService().merge_tables(order_id, table_ids)

    def receiveReadyNotification(self):
        from app.services.kitchen_service import KitchenService
        return KitchenService().ready_items()


class Cashier(User):
    role = "Cashier"

    def handlePayment(self, order, method="cash", discount_amount=0, cash_received=None):
        """Thanh toán một Order; trả về đối tượng Payment đã lưu."""
        from app.models.payment import Payment
        payment = Payment(None, order.order_id, self.user_id, 0, method)
        payment.process(discount_amount, cash_received)
        return payment


class Manager(User):
    role = "Manager"

    def manageMenu(self):
        from app.services.menu_service import MenuService
        return MenuService()

    def manageTables(self):
        from app.services.table_service import TableService
        return TableService()

    def viewRevenue(self, period="day", start=None, end=None):
        from app.services.payment_service import PaymentService
        return PaymentService().revenue_report(period, start, end)

    def viewBestSelling(self, start=None, end=None, limit=10):
        from app.services.payment_service import PaymentService
        return PaymentService().best_selling(start, end, limit)


ROLE_CLASSES = {c.role: c for c in (Kitchen, Waitstaff, Cashier, Manager)}


def user_from_row(row):
    """Tạo đúng lớp con từ một dòng bảng USER (cột role quyết định lớp)."""
    cls = ROLE_CLASSES[row["role"]]
    return cls(row["user_id"], row["username"], row["password_hash"],
               row["full_name"], row["status"])
