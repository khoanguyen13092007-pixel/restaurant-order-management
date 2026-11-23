"""NV1 - Login, logout, role permissions. Codes TC_AUTH_xx match the Testing Document."""
from app.database import get_db
from app.utils.decorators import role_required
from tests.base import AppTestCase


class TestAuth(AppTestCase):
    def test_TC_AUTH_01_login_success_redirects_to_dashboard(self):
        r = self.login("manager", "manager123")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/dashboard"))
        with self.client.session_transaction() as s:
            self.assertEqual(s["role"], "Manager")

    def test_TC_AUTH_02_wrong_password_rejected(self):
        r = self.login("manager", "wrong-password")
        self.assertEqual(r.status_code, 401)
        self.assertIn(b"Invalid username or password.", r.data)
        with self.client.session_transaction() as s:
            self.assertNotIn("user_id", s)

    def test_TC_AUTH_03_unknown_user_rejected_with_same_message(self):
        r = self.login("does-not-exist", "abc")
        self.assertEqual(r.status_code, 401)
        self.assertIn(b"Invalid username or password.", r.data)

    def test_TC_AUTH_04_inactive_account_denied(self):
        r = self.login("inactive", "inactive123")
        self.assertEqual(r.status_code, 401)
        self.assertIn(b"disabled", r.data)

    def test_TC_AUTH_05_empty_fields_rejected(self):
        r = self.login("", "")
        self.assertEqual(r.status_code, 401)

    def test_TC_AUTH_06_password_stored_as_hash(self):
        with self.app.app_context():
            row = get_db().execute(
                'SELECT password_hash FROM "USER" WHERE username="manager"').fetchone()
        self.assertNotEqual(row["password_hash"], "manager123")
        self.assertNotIn("manager123", row["password_hash"])

    def test_TC_AUTH_07_logout_clears_session(self):
        self.login("waiter", "waiter123")
        r = self.client.post("/logout")
        self.assertEqual(r.status_code, 302)
        with self.client.session_transaction() as s:
            self.assertNotIn("user_id", s)
        self.assertEqual(self.client.get("/dashboard").status_code, 302)

    def test_TC_AUTH_08_dashboard_requires_login(self):
        r = self.client.get("/dashboard")
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/login"))

    def test_TC_AUTH_09_wrong_role_gets_403(self):
        @self.app.route("/_manager_only")
        @role_required("Manager")
        def manager_only():
            return "ok"

        self.login("waiter", "waiter123")
        self.assertEqual(self.client.get("/_manager_only").status_code, 403)
        self.client.post("/logout")
        self.login("manager", "manager123")
        self.assertEqual(self.client.get("/_manager_only").status_code, 200)

    def test_TC_AUTH_10_session_is_permanent_for_timeout(self):
        self.login("cashier", "cashier123")
        with self.client.session_transaction() as s:
            self.assertTrue(s.permanent)
        self.assertEqual(self.app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(), 1800)

    def test_TC_AUTH_11_each_role_lands_on_its_own_screen(self):
        expected = {"waiter": ("waiter123", "/tables/"), "kitchen": ("kitchen123", "/kitchen/"),
                    "cashier": ("cashier123", "/payment/"), "manager": ("manager123", "/menu/manage")}
        for user, (password, path) in expected.items():
            b = self.browser()
            b.client.get("/login")
            r = b.client.post("/login", data={"username": user, "password": password},
                              follow_redirects=True)
            self.assertEqual(r.request.path, path, user)

    def test_TC_AUTH_12_login_page_matches_design(self):
        r = self.client.get("/login")
        self.assertIn(b"Staff login", r.data)
        self.assertIn(b"Customers do not need to log in.", r.data)
        self.assertIn(b"View menu as a customer", r.data)
