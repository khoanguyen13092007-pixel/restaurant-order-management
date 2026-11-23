"""NV5 - Totals, payment, invoice, reports. Codes TC_PAY_xx."""
from app.models.order import Order
from app.models.payment import Payment
from app.models.user import Cashier
from app.repositories.user_repository import UserRepository
from app.services import pricing
from app.services.errors import ServiceError
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.table_service import TableService
from tests.base import PHO, T01, T02, TRA_DA, AppTestCase

CASHIER = 4


def _confirmed(item=PHO, qty=2, table_id=None):
    orders = OrderService()
    order_id = orders.create_order(table_id=table_id)
    orders.add_item(order_id, item, qty)
    orders.confirm_order(order_id)
    return order_id


class TestPayment(AppTestCase):
    def test_TC_PAY_01_compute_totals(self):
        with self.app.app_context():
            t = pricing.compute_totals(335000, 0)                   # the example in the GUI design
            self.assertEqual((t["tax_amount"], t["total_amount"]), (33500, 368500))
            t = pricing.compute_totals(130000, 13000)
            self.assertEqual(t, {"subtotal": 130000, "discount_amount": 13000,
                                 "tax_amount": 11700, "total_amount": 128700})
            self.assertEqual(pricing.compute_totals(0, 0)["total_amount"], 0)

    def test_TC_PAY_02_discount_validation(self):
        with self.app.app_context():
            for bad in (-1, "abc", "nan"):
                with self.assertRaises(ServiceError):
                    pricing.parse_discount_amount(bad)
            with self.assertRaises(ServiceError):
                pricing.parse_discount_amount(200000, subtotal=130000)   # more than the subtotal
            self.assertEqual(pricing.parse_discount_amount(""), 0)
            self.assertEqual(pricing.parse_discount_amount("13,000", 130000), 13000)

    def test_TC_PAY_03_preview_does_not_change_order(self):
        with self.app.app_context():
            order_id = _confirmed()
            totals = PaymentService().preview(order_id, 13000)
            self.assertEqual(totals["total_amount"], 128700)
            self.assertEqual(OrderService().get_order(order_id)["order"]["discount_amount"], 0)

    def test_TC_PAY_04_pay_cash_with_change_releases_table(self):
        with self.app.app_context():
            order_id = _confirmed(table_id=T01)
            result = PaymentService().process_payment(order_id, CASHIER, "cash", 0, "150000")
            self.assertEqual(result["total"], 143000)
            self.assertEqual(result["change"], 7000)
            self.assertEqual(OrderService().get_order(order_id)["order"]["status"], "paid")
            self.assertEqual(TableService().get_table(T01)["status"], "available")

    def test_TC_PAY_05_discount_saved_on_order(self):
        with self.app.app_context():
            order_id = _confirmed()
            PaymentService().process_payment(order_id, CASHIER, "card", 13000)
            order = OrderService().get_order(order_id)["order"]
            self.assertEqual((order["discount_amount"], order["total_amount"]), (13000, 128700))

    def test_TC_PAY_06_insufficient_cash_rejected(self):
        with self.app.app_context():
            order_id = _confirmed()
            with self.assertRaises(ServiceError):
                PaymentService().process_payment(order_id, CASHIER, "cash", 0, "100000")
            self.assertEqual(OrderService().get_order(order_id)["order"]["status"], "confirmed")

    def test_TC_PAY_07_cannot_pay_twice(self):
        with self.app.app_context():
            order_id = _confirmed()
            service = PaymentService()
            service.process_payment(order_id, CASHIER, "transfer")
            with self.assertRaises(ServiceError):
                service.process_payment(order_id, CASHIER, "transfer")

    def test_TC_PAY_08_invalid_method_and_unpayable_orders(self):
        with self.app.app_context():
            service, orders = PaymentService(), OrderService()
            order_id = _confirmed()
            with self.assertRaises(ServiceError):
                service.process_payment(order_id, CASHIER, "bitcoin")
            draft = orders.create_order()
            orders.add_item(draft, PHO, 1)
            with self.assertRaises(ServiceError):
                service.process_payment(draft, CASHIER, "cash")      # not confirmed
            orders.add_item(order_id, TRA_DA, 1)
            with self.assertRaises(ServiceError):
                service.process_payment(order_id, CASHIER, "cash")   # has a dish not sent to the kitchen
            with self.assertRaises(ServiceError):
                service.process_payment(9999, CASHIER, "cash")
            with self.assertRaises(ServiceError):
                service.process_payment(order_id, CASHIER, "cash", 99999999)  # discount above subtotal

    def test_TC_PAY_09_invoice_data(self):
        with self.app.app_context():
            order_id = _confirmed(table_id=T01)
            payment_id = PaymentService().process_payment(order_id, CASHIER, "cash")["payment_id"]
            invoice = PaymentService().get_invoice(payment_id)
            self.assertEqual(invoice["payment"]["amount"], 143000)
            self.assertEqual(invoice["cashier_name"], "Cashier Demo")
            self.assertEqual(invoice["tables"][0]["code"], "T01")
            self.assertEqual(len(invoice["items"]), 1)

    def test_TC_PAY_10_cashier_model_handle_payment(self):
        with self.app.app_context():
            order = Order.from_row(OrderService().get_order(_confirmed())["order"])
            cashier = UserRepository().find_by_username("cashier")
            self.assertIsInstance(cashier, Cashier)
            payment = cashier.handlePayment(order, "card", discount_amount=13000)
            self.assertIsInstance(payment, Payment)
            self.assertEqual((payment.amount, payment.status), (128700, "paid"))
            self.assertEqual(payment.printInvoice()["order"]["status"], "paid")

    def test_TC_PAY_17_find_order_by_table(self):
        with self.app.app_context():
            service, orders = PaymentService(), OrderService()
            with self.assertRaises(ServiceError):
                service.order_for_table(T02)                          # no open order
            draft = orders.create_order(table_id=T02)
            orders.add_item(draft, PHO, 1)
            with self.assertRaises(ServiceError):
                service.order_for_table(T02)                          # not confirmed yet
            orders.confirm_order(draft)
            self.assertEqual(service.order_for_table(T02), draft)
            self.assertEqual([t["code"] for t in service.payable_tables()], ["T02"])

    def test_TC_PAY_18_cashier_screen_matches_design(self):
        with self.app.app_context():
            order_id = _confirmed(table_id=T01)
        cashier = self.browser("cashier", "cashier123")
        page = cashier.get(f"/payment/?table={T01}").data
        for text in (b"Find order", b"Bill", b"Subtotal", b"Discount", b"Tax (10%)", b"Total", b"Payment method",
                     b"Bank transfer", b"Confirm payment", b"Print invoice", b"143,000"):
            self.assertIn(text, page)
        self.assertNotIn(b"/payment/invoice/", page)                    # Print invoice is disabled before payment
        r = cashier.post(f"/payment/{order_id}/pay", {"method": "card", "discount": "13000", "table_id": T01})
        self.assertIn(f"/payment/?order={order_id}", r.headers["Location"])
        done = cashier.get(r.headers["Location"]).data
        self.assertIn(b"/payment/invoice/", done)                       # now the invoice can be printed
        self.assertIn(b"128,700", done)


class TestReports(AppTestCase):
    def _two_paid_orders(self):
        service = PaymentService()
        service.process_payment(_confirmed(PHO, 2), CASHIER, "cash")      # 143,000
        service.process_payment(_confirmed(TRA_DA, 1), CASHIER, "card")   # 22,000

    def test_TC_PAY_11_revenue_by_day(self):
        with self.app.app_context():
            self._two_paid_orders()
            report = PaymentService().revenue_report("day")
            self.assertEqual(report["total_revenue"], 165000)
            self.assertEqual(report["total_payments"], 2)
            self.assertEqual(len(report["rows"]), 1)

    def test_TC_PAY_12_revenue_by_week_and_month(self):
        with self.app.app_context():
            self._two_paid_orders()
            for period in ("week", "month"):
                self.assertEqual(PaymentService().revenue_report(period)["total_revenue"], 165000)

    def test_TC_PAY_13_best_selling_sorted_by_quantity(self):
        with self.app.app_context():
            self._two_paid_orders()
            best = PaymentService().best_selling(limit=5)
            self.assertEqual([b["name"] for b in best], ["Beef pho", "Iced tea"])
            self.assertEqual(best[0]["quantity"], 2)
            self.assertEqual(len(PaymentService().best_selling(limit=1)), 1)

    def test_TC_PAY_14_report_excludes_unpaid_and_out_of_range(self):
        with self.app.app_context():
            _confirmed()  # not paid
            self.assertEqual(PaymentService().revenue_report("day")["total_revenue"], 0)
            self._two_paid_orders()
            empty = PaymentService().revenue_report("day", "2000-01-01", "2000-01-31")
            self.assertEqual(empty["total_payments"], 0)

    def test_TC_PAY_15_report_input_validation(self):
        with self.app.app_context():
            service = PaymentService()
            with self.assertRaises(ServiceError):
                service.revenue_report("year")
            with self.assertRaises(ServiceError):
                service.revenue_report("day", "not-a-date", "2026-01-01")
            with self.assertRaises(ServiceError):
                service.revenue_report("day", "2026-02-01", "2026-01-01")
            with self.assertRaises(ServiceError):
                service.best_selling(limit=0)

    def test_TC_PAY_16_pages_respect_roles(self):
        with self.app.app_context():
            _confirmed(table_id=T01)
        self.login("waiter", "waiter123")
        self.assertEqual(self.client.get("/payment/").status_code, 403)
        self.assertEqual(self.client.get("/payment/reports").status_code, 403)
        self.client.post("/logout")
        self.login("cashier", "cashier123")
        self.assertEqual(self.client.get("/payment/").status_code, 200)
        self.assertEqual(self.client.get(f"/payment/?table={T01}&discount=13000").status_code, 200)
        self.assertEqual(self.client.get("/payment/reports").status_code, 403)
        self.client.post("/logout")
        self.login("manager", "manager123")
        self.assertEqual(self.client.get("/payment/reports").status_code, 200)
        self.assertEqual(self.client.get("/payment/reports?period=bad").status_code, 200)

    def test_TC_PAY_19_report_screen_matches_design(self):
        with self.app.app_context():
            self._two_paid_orders()
        manager = self.browser("manager", "manager123")
        page = manager.get("/payment/reports?period=week").data
        for text in (b"Day", b"Week", b"Month", b"From", b"Apply", b"Total revenue", b"165,000",
                     b"Orders paid", b"Revenue per week", b"Best-selling items", b"Rank", b"Beef pho", b"Sold"):
            self.assertIn(text, page)
        self.assertIn(b'class="bar"', page)                               # the revenue chart
