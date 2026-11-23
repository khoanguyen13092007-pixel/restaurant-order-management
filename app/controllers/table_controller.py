"""NV2 - Table routes: the Tables screen (waitstaff) and the Tables tab (manager)."""
from flask import Blueprint, redirect, render_template, request, url_for

from app.services.errors import ServiceError
from app.services.kitchen_service import KitchenService
from app.services.order_service import OrderService
from app.services.table_service import TableService
from app.utils.decorators import role_required
from app.utils.web import attempt

bp = Blueprint("tables", __name__, url_prefix="/tables")


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _back(order_id):
    return redirect(url_for("tables.screen", order=order_id) if order_id else url_for("tables.screen"))


@bp.route("/")
@role_required("Waitstaff", "Manager")
def screen():
    """Tables and Orders: table cards on the left, the selected order on the right."""
    service = TableService()
    order_id, target_id = _int(request.args.get("order")), _int(request.args.get("target"))
    selected = None
    if order_id:
        try:
            selected = OrderService().get_order(order_id)
        except ServiceError:
            order_id = None
    own_tables = {t["table_id"] for t in selected["tables"]} if selected else set()

    cards = []
    for t in service.list_tables():
        if t["active_order_id"]:
            if order_id and t["active_order_id"] != order_id:
                href = url_for("tables.screen", order=order_id, target=t["table_id"])
            else:
                href = url_for("tables.screen", order=t["active_order_id"])
        elif order_id:
            href = url_for("tables.screen", order=order_id, target=t["table_id"])
        else:
            href = url_for("tables.screen", target=t["table_id"])
        cards.append(dict(t, href=href, is_target=(t["table_id"] == target_id),
                          in_order=(t["table_id"] in own_tables)))

    target = next((c for c in cards if c["is_target"]), None)
    ready = KitchenService().ready_items()
    return render_template("tables/screen.html", cards=cards, selected=selected, target=target,
                           order_id=order_id, notification=ready[0] if ready else None,
                           more_ready=max(len(ready) - 1, 0))


@bp.post("/assign")
@role_required("Waitstaff", "Manager")
def assign():
    order_id = _int(request.form.get("order_id"))

    def action():
        order = OrderService().get_order(order_id)
        if order["tables"]:
            raise ServiceError("This order already has a table. Use 'Move order' or 'Merge tables'.")
        TableService().assign_table(order_id, _int(request.form.get("table_id")))
    attempt(action, "Order assigned to the table.")
    return _back(order_id)


@bp.post("/move")
@role_required("Waitstaff", "Manager")
def move():
    order_id = _int(request.form.get("order_id"))

    def action():
        tables = OrderService().get_order(order_id)["tables"]
        if len(tables) != 1:
            raise ServiceError("Move order needs an order with exactly one table.")
        TableService().move_table(order_id, tables[0]["table_id"], _int(request.form.get("table_id")))
    attempt(action, "Order moved.")
    return _back(order_id)


@bp.post("/merge")
@role_required("Waitstaff", "Manager")
def merge():
    order_id = _int(request.form.get("order_id"))
    table_id = _int(request.form.get("table_id"))
    attempt(lambda: TableService().merge_tables(order_id, [table_id] if table_id else []),
            "Tables merged.")
    return _back(order_id)


# ----- Manager: tab 'Tables' -----
@bp.route("/manage")
@role_required("Manager")
def manage():
    service = TableService()
    edit = None
    edit_id = _int(request.args.get("edit"))
    if edit_id:
        try:
            edit = service.get_table(edit_id)
        except ServiceError:
            edit = None
    return render_template("tables/manage.html", tables=service.list_tables(), edit=edit,
                           adding=bool(request.args.get("new")) and edit is None)


@bp.post("/save")
@role_required("Manager")
def save():
    table_id = _int(request.form.get("table_id"))
    service = TableService()
    if table_id:
        ok, _ = attempt(lambda: service.rename_table(table_id, request.form.get("code")), "Table updated.")
    else:
        ok, _ = attempt(lambda: service.create_table(request.form.get("code")), "Table added.")
    if ok:
        return redirect(url_for("tables.manage"))
    return redirect(url_for("tables.manage", edit=table_id) if table_id else url_for("tables.manage", new=1))


@bp.post("/create")
@role_required("Manager")
def create():
    attempt(lambda: TableService().create_table(request.form.get("code")), "Table added.")
    return redirect(url_for("tables.manage"))


@bp.post("/<int:table_id>/delete")
@role_required("Manager")
def delete(table_id):
    attempt(lambda: TableService().delete_table(table_id), "Table deleted.")
    return redirect(url_for("tables.manage"))
    
