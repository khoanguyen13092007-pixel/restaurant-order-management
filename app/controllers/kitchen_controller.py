"""NV4 - Kitchen screen and ready notifications."""
from flask import Blueprint, redirect, render_template, request, url_for

from app.services.kitchen_service import KitchenService
from app.utils.decorators import role_required
from app.utils.web import attempt

bp = Blueprint("kitchen", __name__, url_prefix="/kitchen")

FILTERS = {"": None, "received": "pending", "cooking": "preparing", "done": "ready"}


@bp.route("/")
@role_required("Kitchen")
def board():
    current = request.args.get("status", "")
    if current not in FILTERS:
        current = ""
    return render_template("kitchen/board.html", items=KitchenService().board(FILTERS[current]),
                           current=current)


@bp.post("/items/<int:item_id>/status")
@role_required("Kitchen")
def update_status(item_id):
    attempt(lambda: KitchenService().update_item_status(item_id, request.form.get("status")))
    return redirect(url_for("kitchen.board", status=request.form.get("filter", "")))


@bp.route("/ready")
@role_required("Waitstaff")
def ready():
    return render_template("kitchen/ready.html", items=KitchenService().ready_items())


@bp.post("/items/<int:item_id>/served")
@role_required("Waitstaff")
def served(item_id):
    """'Dismiss' on the notification banner / 'Served' button: the dish was brought to the table."""
    attempt(lambda: KitchenService().mark_served(item_id))
    target = request.form.get("next", "")
    if not target.startswith("/") or target.startswith("//"):  # only local paths (no open redirect)
        target = url_for("kitchen.ready")
    return redirect(target)
