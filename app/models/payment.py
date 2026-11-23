"""NV5 - Payment (class diagram mục 5.2)."""


class Payment:
    def __init__(self, payment_id, order_id, cashier_id, amount, method,
                 status="pending", paid_at=None):
        self.payment_id = payment_id
        self.order_id = order_id
        self.cashier_id = cashier_id
        self.amount = amount
        self.method = method
        self.status = status
        self.paid_at = paid_at

    @classmethod
    def from_row(cls, row):
        return cls(row["payment_id"], row["order_id"], row["cashier_id"], row["amount"],
                   row["method"], row["status"], row["paid_at"])

    def process(self, discount_amount=0, cash_received=None):
        """Thanh toán đơn; cập nhật payment_id, amount, status, paid_at cho đối tượng."""
        from app.services.payment_service import PaymentService
        service = PaymentService()
        result = service.process_payment(self.order_id, self.cashier_id, self.method,
                                         discount_amount, cash_received)
        saved = service.get_invoice(result["payment_id"])["payment"]
        self.__dict__.update(Payment.from_row(saved).__dict__)
        return result

    def printInvoice(self):
        """Trả về dữ liệu hoá đơn (giao diện /payment/invoice/<id> dùng để in)."""
        from app.services.payment_service import PaymentService
        return PaymentService().get_invoice(self.payment_id)
