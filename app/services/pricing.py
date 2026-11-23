"""NV5 (FR-11) - Subtotal, discount, tax, total. Shared by NV3 and NV5."""
import math

from flask import current_app

from app.repositories.order_repository import OrderItemRepository, OrderRepository
from app.services.errors import ServiceError


def _round(x):
    return int(math.floor(x + 0.5))


def parse_discount_amount(value, subtotal=None):
    """The discount is an amount in VND (the GUI design has a 'Discount [ 0 ] VND' field)."""
    if value in (None, ""):
        return 0
    try:
        amount = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise ServiceError("Discount must be a number.")
    if not math.isfinite(amount) or amount < 0:
        raise ServiceError("Discount must be zero or more.")
    if subtotal is not None and amount > subtotal:
        raise ServiceError("Discount cannot be larger than the subtotal.")
    return amount


def compute_totals(subtotal, discount_amount=0, tax_rate=None):
    """Pure function: total = (subtotal - discount) + tax, rounded to whole VND."""
    if tax_rate is None:
        tax_rate = current_app.config["TAX_RATE"]
    discount = _round(discount_amount)
    taxable = subtotal - discount
    tax = _round(taxable * tax_rate)
    return {
        "subtotal": subtotal,
        "discount_amount": discount,
        "tax_amount": tax,
        "total_amount": taxable + tax,
    }


def recalculate_order(order_id, discount_amount=0):
    """Recompute and save the order totals from the items that are not cancelled."""
    subtotal = OrderItemRepository().subtotal_of_order(order_id)
    totals = compute_totals(subtotal, min(discount_amount, subtotal))
    OrderRepository().update(order_id, totals)
    return totals
