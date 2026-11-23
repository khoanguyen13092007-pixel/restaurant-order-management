"""NV2 - Menu and tables. Codes TC_MENU_xx, TC_TABLE_xx."""
from app.services.errors import ServiceError
from app.services.menu_service import MenuService
from app.services.order_service import OrderService
from app.services.table_service import TableService
from tests.base import MANGO, PHO, T01, T02, T03, TRA_DA, AppTestCase


class TestMenu(AppTestCase):
    def test_TC_MENU_01_search_ignores_case_and_accents(self):
        with self.app.app_context():
            names = [i["name"] for i in MenuService().search_items("PHO")]
        self.assertEqual(names, ["Beef pho"])

    def test_TC_MENU_02_filter_by_category(self):
        with self.app.app_context():
            service = MenuService()
            drinks = next(c for c in service.list_categories() if c["name"] == "Drinks")
            names = {i["name"] for i in service.search_items(category_id=drinks["category_id"])}
        self.assertEqual(names, {"Iced tea"})

    def test_TC_MENU_03_create_item_validation(self):
        with self.app.app_context():
            service = MenuService()
            cat = service.list_categories()[0]["category_id"]
            new_id = service.create_item(cat, "Tea", "Hot tea", "20000")
            self.assertEqual(service.get_item(new_id)["price"], 20000)
            hidden = service.create_item(cat, "Soup", "", "10000", is_available=False)
            self.assertEqual(service.get_item(hidden)["is_available"], 0)
            for name, price in (("", "10"), ("Dish", "-5"), ("Dish", "abc"), ("Dish", "nan")):
                with self.assertRaises(ServiceError):
                    service.create_item(cat, name, "", price)

    def test_TC_MENU_04_sold_out_item_not_offered(self):
        with self.app.app_context():
            service = MenuService()
            service.set_available(MANGO, False)
            names = {i["name"] for i in service.search_items(only_available=True)}
            self.assertNotIn("Mango pudding", names)
            self.assertNotIn("Fried rice", names)           # sold out in the seed data (as in the design)
            with self.assertRaises(ServiceError):
                OrderService().add_item(OrderService().create_order(), MANGO, 1)

    def test_TC_MENU_05_update_price(self):
        with self.app.app_context():
            service = MenuService()
            service.update_price(TRA_DA, "25000")
            self.assertEqual(service.get_item(TRA_DA)["price"], 25000)
            with self.assertRaises(ServiceError):
                service.update_price(TRA_DA, "-1")

    def test_TC_MENU_06_cannot_delete_item_used_in_order(self):
        with self.app.app_context():
            orders = OrderService()
            orders.add_item(orders.create_order(), PHO, 1)
            service = MenuService()
            with self.assertRaises(ServiceError):
                service.delete_item(PHO)
            service.delete_item(MANGO)  # never used, so it can be deleted
            with self.assertRaises(ServiceError):
                service.get_item(MANGO)

    def test_TC_MENU_07_delete_category_rules(self):
        with self.app.app_context():
            service = MenuService()
            cat = service.list_categories()[0]["category_id"]
            with self.assertRaises(ServiceError):
                service.delete_category(cat)  # still has dishes
            empty = service.create_category("Specials")
            service.delete_category(empty)

    def test_TC_MENU_08_manage_requires_manager(self):
        self.login("waiter", "waiter123")
        self.assertEqual(self.client.get("/menu/manage").status_code, 403)
        self.assertEqual(self.client.post("/menu/category/new", data={"name": "X"}).status_code, 403)
        self.client.post("/logout")
        self.login("manager", "manager123")
        self.assertEqual(self.client.get("/menu/manage").status_code, 200)
        self.client.post("/menu/category/new", data={"name": "Specials"})
        with self.app.app_context():
            self.assertIn("Specials", [c["name"] for c in MenuService().list_categories()])

    def test_TC_MENU_09_menu_page_for_any_staff(self):
        self.login("kitchen", "kitchen123")
        r = self.client.get("/menu/?q=pho")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Beef pho", r.data)

    def test_TC_MENU_10_manager_edit_panel_and_save(self):
        self.login("manager", "manager123")
        page = self.client.get(f"/menu/manage?edit={PHO}")
        self.assertIn(b'value="Beef pho"', page.data)
        self.client.post(f"/menu/item/{PHO}/edit", data={
            "name": "Beef pho special", "category_id": 2, "price": "70000",
            "description": "x", "available": "0"})
        with self.app.app_context():
            item = MenuService().get_item(PHO)
        self.assertEqual((item["name"], item["price"], item["is_available"]),
                         ("Beef pho special", 70000, 0))

    def test_TC_MENU_11_manager_screen_matches_design(self):
        self.login("manager", "manager123")
        page = self.client.get("/menu/manage").data
        for text in (b"+ Add item", b"Manage categories", b"Add / edit item", b"Sold out", b"[Edit]", b"[Delete]"):
            self.assertIn(text, page)


class TestTables(AppTestCase):
    def test_TC_TABLE_01_create_and_rename_rules(self):
        with self.app.app_context():
            service = TableService()
            new_id = service.create_table("T99")
            for code in ("", "   ", "T99", "A B", "A/B"):
                with self.assertRaises(ServiceError):
                    service.create_table(code)
            service.rename_table(new_id, "T98")
            self.assertEqual(service.get_table(new_id)["code"], "T98")
            with self.assertRaises(ServiceError):
                service.rename_table(new_id, "T01")  # already used

    def test_TC_TABLE_02_assign_marks_occupied(self):
        with self.app.app_context():
            orders, tables = OrderService(), TableService()
            order_id = orders.create_order()
            tables.assign_table(order_id, T01)
            self.assertEqual(tables.get_table(T01)["status"], "occupied")
            with self.assertRaises(ServiceError):
                tables.assign_table(orders.create_order(), T01)  # table already has an order

    def test_TC_TABLE_03_move_table(self):
        with self.app.app_context():
            orders, tables = OrderService(), TableService()
            order_id = orders.create_order(table_id=T01)
            tables.move_table(order_id, T01, T02)
            self.assertEqual(tables.get_table(T01)["status"], "available")
            self.assertEqual(tables.get_table(T02)["status"], "occupied")
            self.assertEqual([t["table_id"] for t in tables.tables_of_order(order_id)], [T02])
            with self.assertRaises(ServiceError):
                tables.move_table(order_id, T01, T03)  # T01 no longer belongs to the order

    def test_TC_TABLE_04_merge_free_table(self):
        with self.app.app_context():
            orders, tables = OrderService(), TableService()
            order_id = orders.create_order(table_id=T01)
            tables.merge_tables(order_id, [T02, T03])
            self.assertEqual(len(tables.tables_of_order(order_id)), 3)
            with self.assertRaises(ServiceError):
                tables.merge_tables(order_id, [])

    def test_TC_TABLE_05_merge_table_with_other_order_merges_orders(self):
        with self.app.app_context():
            orders, tables = OrderService(), TableService()
            a = orders.create_order(table_id=T01)
            b = orders.create_order(table_id=T02)
            orders.add_item(a, PHO, 1)
            orders.add_item(b, TRA_DA, 2)
            tables.merge_tables(a, [T02])
            merged = orders.get_order(a)
            self.assertEqual(len(merged["items"]), 2)
            self.assertEqual(merged["order"]["subtotal"], 65000 + 40000)
            self.assertEqual(orders.get_order(b)["order"]["status"], "merged")
            self.assertEqual(orders.get_order(b)["order"]["subtotal"], 0)
            self.assertEqual({t["table_id"] for t in merged["tables"]}, {T01, T02})

    def test_TC_TABLE_06_cannot_delete_busy_or_used_table(self):
        with self.app.app_context():
            orders, tables = OrderService(), TableService()
            orders.create_order(table_id=T01)
            with self.assertRaises(ServiceError):
                tables.delete_table(T01)
            tables.delete_table(T03)  # unused table

    def test_TC_TABLE_07_pages_respect_roles(self):
        self.login("waiter", "waiter123")
        r = self.client.get("/tables/")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Table T01", r.data)
        self.assertEqual(self.client.get("/tables/manage").status_code, 403)
        self.client.post("/logout")
        self.login("kitchen", "kitchen123")
        self.assertEqual(self.client.get("/tables/").status_code, 403)
        self.client.post("/logout")
        self.login("manager", "manager123")
        page = self.client.get("/tables/manage")
        self.assertEqual(page.status_code, 200)
        for text in (b"+ Add table", b"Add / edit table", b"A table that is currently occupied cannot be deleted."):
            self.assertIn(text, page.data)

    def test_TC_TABLE_08_screen_shows_selected_order_and_target(self):
        with self.app.app_context():
            order_id = OrderService().create_order(table_id=T01)
        self.login("waiter", "waiter123")
        page = self.client.get(f"/tables/?order={order_id}&target={T02}").data
        self.assertIn(f"Order #{order_id}".encode(), page)
        self.assertIn(b"Selected: Table T02", page)
        for text in (b"Assign order to table", b"Move order", b"Merge tables"):
            self.assertIn(text, page)

    def test_TC_TABLE_09_move_and_merge_through_the_screen(self):
        with self.app.app_context():
            order_id = OrderService().create_order(table_id=T01)
        waiter = self.browser("waiter", "waiter123")
        waiter.post("/tables/move", {"order_id": order_id, "table_id": T02})
        waiter.post("/tables/merge", {"order_id": order_id, "table_id": T03})
        with self.app.app_context():
            codes = sorted(t["code"] for t in TableService().tables_of_order(order_id))
        self.assertEqual(codes, ["T02", "T03"])

    def test_TC_TABLE_10_manager_saves_table(self):
        manager = self.browser("manager", "manager123")
        manager.post("/tables/save", {"table_id": "", "code": "T20"})
        with self.app.app_context():
            self.assertEqual(TableService().get_by_code("T20")["status"], "available")
