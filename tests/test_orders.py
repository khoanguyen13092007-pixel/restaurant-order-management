"""NV3 - Orders and customer self-ordering. Codes TC_ORDER_xx."""
from app.models.order import Order, OrderItem
from app.models.user import Waitstaff
from app.repositories.user_repository import UserRepository
from app.services.errors import ServiceError
from app.services.kitchen_service import KitchenService
from app.services.order_service import OrderService
from app.services.table_service import TableService
from tests.base import COM_RANG, GOI_CUON, MANGO, PHO, T01, TRA_DA, AppTestCase


class TestOrders(AppTestCase):
    def test_TC_ORDER_01_create_order_with_table(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order(waitstaff_id=2, table_id=T01, note="VIP guest")
            data = service.get_order(order_id)
            self.assertEqual(data["order"]["status"], "draft")
            self.assertEqual(data["tables"][0]["code"], "T01")
            self.assertEqual(TableService().get_table(T01)["status"], "occupied")

    def test_TC_ORDER_02_totals_include_tax(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            service.add_item(order_id, PHO, 2)
            order = service.get_order(order_id)["order"]
            self.assertEqual(order["subtotal"], 130000)
            self.assertEqual(order["tax_amount"], 13000)       # tax rate 10% as in the design
            self.assertEqual(order["total_amount"], 143000)

    def test_TC_ORDER_03_invalid_quantity_rejected(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            for qty in (0, -1, 51, "abc", ""):
                with self.assertRaises(ServiceError):
                    service.add_item(order_id, PHO, qty)
            with self.assertRaises(ServiceError):
                service.add_item(order_id, 999, 1)  # dish does not exist
            with self.assertRaises(ServiceError):
                service.add_item(order_id, COM_RANG, 1)  # sold out

    def test_TC_ORDER_04_edit_and_cancel_item_before_cooking(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            item = service.add_item(order_id, PHO, 1)
            service.update_quantity(item, 3)
            self.assertEqual(service.get_order(order_id)["order"]["subtotal"], 195000)
            service.cancel_item(item)
            self.assertEqual(service.get_order(order_id)["order"]["subtotal"], 0)

    def test_TC_ORDER_05_cannot_edit_item_after_kitchen_started(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            item = service.add_item(order_id, PHO, 1)
            service.confirm_order(order_id)
            KitchenService().update_item_status(item, "preparing")
            with self.assertRaises(ServiceError):
                service.update_quantity(item, 2)
            with self.assertRaises(ServiceError):
                service.cancel_item(item)

    def test_TC_ORDER_06_confirm_sends_ticket_to_kitchen(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            with self.assertRaises(ServiceError):
                service.confirm_order(order_id)  # no dishes yet
            service.add_item(order_id, PHO, 1)
            service.add_item(order_id, TRA_DA, 1)
            ticket_id = service.confirm_order(order_id, waitstaff_id=2)
            data = service.get_order(order_id)
            self.assertEqual(data["order"]["status"], "confirmed")
            self.assertEqual(data["order"]["waitstaff_id"], 2)
            self.assertTrue(all(i["ticket_id"] == ticket_id for i in data["items"]))
            with self.assertRaises(ServiceError):
                service.confirm_order(order_id)  # confirm pressed a second time

    def test_TC_ORDER_07_new_items_on_confirmed_order_get_new_ticket(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            service.add_item(order_id, PHO, 1)
            first = service.confirm_order(order_id)
            service.add_item(order_id, MANGO, 1)
            self.assertEqual(service.get_order(order_id)["unsent"], 1)
            second = service.confirm_order(order_id)
            self.assertNotEqual(first, second)
            self.assertEqual(service.get_order(order_id)["unsent"], 0)

    def test_TC_ORDER_08_cancel_order_releases_table(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order(table_id=T01)
            service.add_item(order_id, PHO, 1)
            service.confirm_order(order_id)
            service.cancel_order(order_id)
            self.assertEqual(service.get_order(order_id)["order"]["status"], "cancelled")
            self.assertEqual(TableService().get_table(T01)["status"], "available")
            with self.assertRaises(ServiceError):
                service.add_item(order_id, PHO, 1)  # order is cancelled

    def test_TC_ORDER_09_cannot_cancel_order_once_cooking(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.create_order()
            item = service.add_item(order_id, PHO, 1)
            service.confirm_order(order_id)
            KitchenService().update_item_status(item, "preparing")
            with self.assertRaises(ServiceError):
                service.cancel_order(order_id)

    def test_TC_ORDER_10_models_follow_class_diagram(self):
        with self.app.app_context():
            waiter = UserRepository().find_by_username("waiter")
            self.assertIsInstance(waiter, Waitstaff)
            order = waiter.createOrder(table_id=T01)
            self.assertIsInstance(order, Order)
            item_id = order.addItem(PHO, 2)
            self.assertEqual(order.subtotal, 130000)
            item = OrderItem.from_row(OrderService().get_order(order.order_id)["items"][0])
            self.assertTrue(item.canModify())
            self.assertEqual(item.getSubtotal(), 130000)
            order.confirm(waiter.user_id)
            self.assertEqual(order.status, "confirmed")
            waiter.editOrCancelItem(item_id, quantity=3)
            order.calculateTotal()
            self.assertEqual(order.subtotal, 195000)

    # ----- customer self-ordering (FR-06) -----
    def test_TC_ORDER_11_customer_places_order_at_table(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.place_customer_order(
                "T01", [{"menu_item_id": PHO, "quantity": "2"},
                        {"menu_item_id": TRA_DA, "quantity": "0"}], "An", "0900")
            data = service.get_order(order_id)
            self.assertEqual(data["order"]["status"], "draft")   # waits for the waitstaff
            self.assertEqual(len(data["items"]), 1)
            self.assertEqual(data["tables"][0]["code"], "T01")
            self.assertIsNotNone(data["order"]["customer_id"])

    def test_TC_ORDER_12_customer_adds_to_existing_order_of_table(self):
        with self.app.app_context():
            service = OrderService()
            first = service.place_customer_order("T01", [{"menu_item_id": PHO, "quantity": "1"}])
            second = service.place_customer_order("T01", [{"menu_item_id": GOI_CUON, "quantity": "1"}])
            self.assertEqual(first, second)
            self.assertEqual(len(service.get_order(first)["items"]), 2)

    def test_TC_ORDER_13_customer_order_validation(self):
        with self.app.app_context():
            service = OrderService()
            with self.assertRaises(ServiceError):
                service.place_customer_order("T01", [{"menu_item_id": PHO, "quantity": "0"}])
            with self.assertRaises(ServiceError):
                service.place_customer_order("NO-SUCH", [{"menu_item_id": PHO, "quantity": "1"}])
            with self.assertRaises(ServiceError):
                service.place_customer_order("T01", [{"menu_item_id": PHO, "quantity": "1"},
                                                     {"menu_item_id": 999, "quantity": "1"}])
            with self.assertRaises(ServiceError):
                service.place_customer_order("T01", [{"menu_item_id": COM_RANG, "quantity": "1"}])
            self.assertEqual(len(service.list_orders()), 0)   # an error creates no order

    def test_TC_ORDER_14_customer_page_needs_no_login(self):
        r = self.client.get("/customer/T01")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Beef pho", r.data)
        self.assertIn(b"Current order", r.data)
        self.assertEqual(self.client.get("/customer/").status_code, 200)     # 'View menu as a customer'
        self.assertEqual(self.client.get("/customer/NO-SUCH").status_code, 404)

    def test_TC_ORDER_15_duplicate_submit_creates_one_order(self):
        waiter = self.browser("waiter", "waiter123")
        data = {"request_token": "abc123", "table_code": "T01", f"qty_{PHO}": "1"}
        waiter.post("/orders/new", data)
        waiter.post("/orders/new", data)  # same token sent again
        with self.app.app_context():
            self.assertEqual(len(OrderService().list_orders()), 1)

    def test_TC_ORDER_16_duplicate_customer_submit_creates_one_order(self):
        guest = self.browser()
        guest.get("/customer/T01")
        data = {"request_token": "zzz", "table_code": "T01", f"qty_{PHO}": "1"}
        guest.post("/customer/T01", data)
        guest.post("/customer/T01", data)
        with self.app.app_context():
            orders = OrderService().list_orders()
            self.assertEqual(len(orders), 1)
            self.assertEqual(len(OrderService().get_order(orders[0]["order_id"])["items"]), 1)

    def test_TC_ORDER_17_order_pages_require_staff_role(self):
        self.assertEqual(self.client.get("/orders/new").status_code, 302)  # not logged in
        self.login("kitchen", "kitchen123")
        self.assertEqual(self.client.get("/orders/new").status_code, 403)
        self.client.post("/logout")
        self.login("waiter", "waiter123")
        page = self.client.get("/orders/new?table=T02")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'value="T02" selected', page.data)
        self.assertEqual(self.client.get("/orders/").status_code, 302)    # goes to the Tables screen

    def test_TC_ORDER_18_staff_order_is_confirmed_and_sent_to_kitchen(self):
        with self.app.app_context():
            service = OrderService()
            order_id = service.place_order_at_table(
                "T03", [{"menu_item_id": PHO, "quantity": "2"}], note="no onion",
                waitstaff_id=2, confirm=True)
            data = service.get_order(order_id)
            self.assertEqual(data["order"]["status"], "confirmed")
            self.assertEqual(data["items"][0]["note"], "no onion")   # the kitchen sees the note
            self.assertEqual(KitchenService().board()[0]["note"], "no onion")

    def test_TC_ORDER_19_screen_has_cart_and_filters_from_design(self):
        self.login("waiter", "waiter123")
        page = self.client.get("/orders/new").data
        for text in (b"Search dish by name...", b"Appetizers", b"Main dishes", b"Drinks", b"Fried rice (sold out)",
                     b"Current order", b"Subtotal:", b"Confirm order &amp; send to kitchen"):
            self.assertIn(text, page)
