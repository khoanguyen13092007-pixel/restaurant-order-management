"""End-to-end through HTTP with CSRF on: customer orders -> waitstaff confirms -> kitchen cooks ->
waitstaff serves -> cashier pays -> manager reads the report."""
from app.services.order_service import OrderService
from tests.base import PHO, TRA_DA, AppTestCase


class TestFullFlow(AppTestCase):
    csrf = True

    def test_TC_FLOW_01_csrf_blocks_post_without_token(self):
        self.client.get("/login")
        r = self.client.post("/login", data={"username": "manager", "password": "manager123"})
        self.assertEqual(r.status_code, 400)
        r = self.client.post("/login", data={"username": "manager", "password": "manager123",
                                              "_csrf": "wrong-token"})
        self.assertEqual(r.status_code, 400)

    def test_TC_FLOW_02_end_to_end(self):
        guest = self.browser()
        waiter = self.browser("waiter", "waiter123")
        kitchen = self.browser("kitchen", "kitchen123")
        cashier = self.browser("cashier", "cashier123")
        manager = self.browser("manager", "manager123")

        # 1. The customer at table T01 orders 2 Beef pho + 1 Iced tea (subtotal 150,000 as in the design)
        guest.get("/customer/T01")
        r = guest.post("/customer/T01", {"request_token": "t1", "table_code": "T01", "note": "no onion",
                                         f"qty_{PHO}": "2", f"qty_{TRA_DA}": "1"})
        self.assertEqual(r.status_code, 302)
        with self.app.app_context():
            order_id = OrderService().list_orders()[0]["order_id"]
            self.assertEqual(OrderService().get_order(order_id)["order"]["status"], "draft")

        # 2. The waitstaff sees the table occupied with that order, and confirms it
        screen = waiter.get("/tables/").data
        self.assertIn(f"Order #{order_id}".encode(), screen)
        self.assertIn(b"Not sent", waiter.get(f"/tables/?order={order_id}").data)
        waiter.post(f"/orders/{order_id}/confirm")
        with self.app.app_context():
            data = OrderService().get_order(order_id)
            self.assertEqual(data["order"]["status"], "confirmed")
            item_ids = [i["order_item_id"] for i in data["items"]]

        # 3. The kitchen cooks every dish
        self.assertIn(b"no onion", kitchen.get("/kitchen/").data)
        for item_id in item_ids:
            kitchen.post(f"/kitchen/items/{item_id}/status", {"status": "preparing"})
            kitchen.post(f"/kitchen/items/{item_id}/status", {"status": "ready"})

        # 4. The waitstaff gets the notification and dismisses it as each dish is served
        self.assertIn(b"is ready to serve", waiter.get("/tables/").data)
        for item_id in item_ids:
            waiter.post(f"/kitchen/items/{item_id}/served", {"next": "/tables/"})
        self.assertNotIn(b"is ready to serve", waiter.get("/tables/").data)

        # 5. The cashier finds the order by table, sees the bill (150,000 + 10% tax = 165,000), pays
        bill = cashier.get("/payment/?table=1").data
        self.assertIn(b"165,000", bill)
        self.assertIn(b"150,000", bill)
        r = cashier.post(f"/payment/{order_id}/pay", {"method": "cash", "discount": "0", "table_id": "1"})
        self.assertEqual(r.status_code, 302)
        paid_screen = cashier.get(r.headers["Location"]).data
        self.assertIn(b"/payment/invoice/", paid_screen)
        invoice_url = paid_screen.split(b'href="')[-1].split(b'"')[0].decode()
        invoice = cashier.get(invoice_url)
        self.assertIn(b"INVOICE", invoice.data)
        self.assertIn(b"Beef pho", invoice.data)

        # 5b. Table T01 is available again
        with self.app.app_context():
            self.assertEqual(OrderService().get_order(order_id)["order"]["status"], "paid")
        self.assertIn(b"Available", waiter.get("/tables/").data)

        # 6. The manager reads the report
        report = manager.get("/payment/reports").data
        self.assertIn(b"Beef pho", report)
        self.assertIn(b"165,000", report)
