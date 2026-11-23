"""NV4 - Kitchen and ready notifications. Codes TC_KITCHEN_xx."""
from app.models.user import Kitchen
from app.repositories.user_repository import UserRepository
from app.services.errors import ServiceError
from app.services.kitchen_service import KitchenService
from app.services.order_service import OrderService
from tests.base import PHO, T01, TRA_DA, AppTestCase


def _confirmed_order(table_id=None):
    orders = OrderService()
    order_id = orders.create_order(table_id=table_id)
    a = orders.add_item(order_id, PHO, 1)
    b = orders.add_item(order_id, TRA_DA, 2)
    orders.confirm_order(order_id)
    return order_id, a, b


class TestKitchen(AppTestCase):
    def test_TC_KITCHEN_01_only_confirmed_orders_reach_kitchen(self):
        with self.app.app_context():
            orders = OrderService()
            draft = orders.create_order()
            orders.add_item(draft, PHO, 1)
            self.assertEqual(len(KitchenService().items_to_prepare()), 0)
            _confirmed_order(table_id=T01)
            rows = KitchenService().items_to_prepare()
            self.assertEqual({r["item_name"] for r in rows}, {"Beef pho", "Iced tea"})
            self.assertEqual(rows[0]["table_codes"], "T01")

    def test_TC_KITCHEN_02_status_flow(self):
        with self.app.app_context():
            _, a, _ = _confirmed_order()
            kitchen = KitchenService()
            kitchen.update_item_status(a, "preparing")
            kitchen.update_item_status(a, "ready")
            self.assertEqual(len(kitchen.ready_items()), 1)
            self.assertEqual(kitchen.ready_items()[0]["item_name"], "Beef pho")

    def test_TC_KITCHEN_03_cannot_skip_or_go_backwards(self):
        with self.app.app_context():
            _, a, _ = _confirmed_order()
            kitchen = KitchenService()
            with self.assertRaises(ServiceError):
                kitchen.update_item_status(a, "ready")        # skips 'cooking'
            kitchen.update_item_status(a, "preparing")
            with self.assertRaises(ServiceError):
                kitchen.update_item_status(a, "preparing")    # repeated
            with self.assertRaises(ServiceError):
                kitchen.update_item_status(a, "served")       # the kitchen cannot mark served
            with self.assertRaises(ServiceError):
                kitchen.update_item_status(9999, "preparing")

    def test_TC_KITCHEN_04_ticket_status_follows_items(self):
        with self.app.app_context():
            from app.repositories.kitchen_repository import KitchenTicketRepository
            _, a, b = _confirmed_order()
            kitchen, tickets = KitchenService(), KitchenTicketRepository()
            ticket_id = kitchen.items_to_prepare()[0]["ticket_id"]
            self.assertEqual(tickets.get_by_id(ticket_id)["status"], "received")
            kitchen.update_item_status(a, "preparing")
            self.assertEqual(tickets.get_by_id(ticket_id)["status"], "preparing")
            for item in (a, b):
                if item != a:
                    kitchen.update_item_status(item, "preparing")
                kitchen.update_item_status(item, "ready")
            self.assertEqual(tickets.get_by_id(ticket_id)["status"], "done")

    def test_TC_KITCHEN_05_ready_notification_and_served(self):
        with self.app.app_context():
            _, a, _ = _confirmed_order(table_id=T01)
            kitchen = KitchenService()
            kitchen.update_item_status(a, "preparing")
            with self.assertRaises(ServiceError):
                kitchen.mark_served(a)  # not finished yet
            kitchen.update_item_status(a, "ready")
            self.assertEqual(kitchen.ready_items()[0]["table_codes"], "T01")
            kitchen.mark_served(a)
            self.assertEqual(kitchen.ready_items(), [])
            with self.assertRaises(ServiceError):
                kitchen.mark_served(a)

    def test_TC_KITCHEN_06_cancelled_item_not_shown_to_kitchen(self):
        with self.app.app_context():
            _, a, _ = _confirmed_order()
            OrderService().cancel_item(a)
            names = {r["item_name"] for r in KitchenService().items_to_prepare()}
            self.assertEqual(names, {"Iced tea"})

    def test_TC_KITCHEN_07_kitchen_model(self):
        with self.app.app_context():
            _, a, _ = _confirmed_order()
            kitchen = UserRepository().find_by_username("kitchen")
            self.assertIsInstance(kitchen, Kitchen)
            self.assertEqual(len(kitchen.viewItemsToPrepare()), 2)
            kitchen.updateItemStatus(a, "preparing")
            self.assertEqual(KitchenService().items_to_prepare()[0]["status"], "preparing")

    def test_TC_KITCHEN_08_pages_respect_roles(self):
        with self.app.app_context():
            _confirmed_order()
        self.login("waiter", "waiter123")
        self.assertEqual(self.client.get("/kitchen/").status_code, 403)
        self.assertEqual(self.client.get("/kitchen/ready").status_code, 200)
        self.client.post("/logout")
        self.login("kitchen", "kitchen123")
        self.assertEqual(self.client.get("/kitchen/").status_code, 200)
        self.assertEqual(self.client.get("/kitchen/ready").status_code, 403)
        self.assertIn(b"Beef pho", self.client.get("/kitchen/").data)

    def test_TC_KITCHEN_09_board_lists_done_items_and_filters(self):
        with self.app.app_context():
            _, a, b = _confirmed_order()
            kitchen = KitchenService()
            kitchen.update_item_status(a, "preparing")
            kitchen.update_item_status(a, "ready")
            kitchen.update_item_status(b, "preparing")
            self.assertEqual(len(kitchen.board()), 2)                       # Cooking + Done
            self.assertEqual([r["item_name"] for r in kitchen.board("ready")], ["Beef pho"])
            self.assertEqual([r["item_name"] for r in kitchen.board("preparing")], ["Iced tea"])
            kitchen.mark_served(a)
            self.assertEqual(len(kitchen.board()), 1)                       # served items leave the board

    def test_TC_KITCHEN_10_screen_matches_design(self):
        with self.app.app_context():
            _confirmed_order(table_id=T01)
        kitchen = self.browser("kitchen", "kitchen123")
        page = kitchen.get("/kitchen/").data
        for text in (b"All", b"Received", b"Cooking", b"Done", b"[Start cooking]", b"T01"):
            self.assertIn(text, page)
        self.assertNotIn(b"[Mark done]", page)
        with self.app.app_context():
            item = KitchenService().board()[0]["order_item_id"]
        kitchen.post(f"/kitchen/items/{item}/status", {"status": "preparing"})
        self.assertIn(b"[Mark done]", kitchen.get("/kitchen/?status=cooking").data)

    def test_TC_KITCHEN_11_dismiss_banner_marks_served(self):
        with self.app.app_context():
            _, a, _ = _confirmed_order(table_id=T01)
            KitchenService().update_item_status(a, "preparing")
            KitchenService().update_item_status(a, "ready")
        waiter = self.browser("waiter", "waiter123")
        page = waiter.get("/tables/").data
        self.assertIn(b"Table T01: Beef pho is ready to serve.", page)
        r = waiter.post(f"/kitchen/items/{a}/served", {"next": "/tables/"})
        self.assertTrue(r.headers["Location"].endswith("/tables/"))
        self.assertNotIn(b"is ready to serve", waiter.get("/tables/").data)
        r = waiter.post(f"/kitchen/items/{a}/served", {"next": "https://evil.example/"})
        self.assertNotIn("evil.example", r.headers["Location"])           # no open redirect
