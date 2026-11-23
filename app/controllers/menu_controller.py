"""NV2 - Menu routes: view/search (any staff), manage dishes and categories (Manager)."""
from flask import Blueprint, redirect, render_template, request, url_for

from app.services.errors import ServiceError
from app.services.menu_service import MenuService
from app.utils.decorators import login_required, role_required
from app.utils.web import attempt

bp = Blueprint("menu", __name__, url_prefix="/menu")


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@bp.route("/")
@login_required
def list_menu():
    service = MenuService()
    q = request.args.get("q", "")
    category_id = _int(request.args.get("category"))
    items = service.search_items(q, category_id, only_available=False)
    return render_template("menu/list.html", items=items, categories=service.list_categories(),
                           q=q, category_id=category_id)


@bp.route("/manage")
@role_required("Manager")
def manage():
    """Manager screen, tab 'Menu items': list on the left, Add / edit item panel on the right."""
    service = MenuService()
    q = request.args.get("q", "")
    edit = None
    edit_id = _int(request.args.get("edit"))
    if edit_id:
        try:
            edit = service.get_item(edit_id)
        except ServiceError:
            edit = None
    return render_template("menu/manage.html", categories=service.list_categories(),
                           items=service.search_items(q), q=q, edit=edit,
                           adding=bool(request.args.get("new")) and edit is None)


def _form_available():
    return request.form.get("available", "1") == "1"


@bp.post("/item/new")
@role_required("Manager")
def item_new():
    f = request.form
    ok, _ = attempt(lambda: MenuService().create_item(
        _int(f.get("category_id")), f.get("name"), f.get("description"), f.get("price"),
        _form_available()), "Dish added.")
    return redirect(url_for("menu.manage") if ok else url_for("menu.manage", new=1))


@bp.route("/item/<int:item_id>/edit", methods=["GET", "POST"])
@role_required("Manager")
def item_edit(item_id):
    if request.method == "POST":
        f = request.form
        ok, _ = attempt(lambda: MenuService().update_item(
            item_id, _int(f.get("category_id")), f.get("name"), f.get("description"),
            f.get("price"), _form_available()), "Dish updated.")
        return redirect(url_for("menu.manage") if ok else url_for("menu.manage", edit=item_id))
    return redirect(url_for("menu.manage", edit=item_id))


@bp.post("/item/<int:item_id>/toggle")
@role_required("Manager")
def item_toggle(item_id):
    def action():
        service = MenuService()
        service.set_available(item_id, not service.get_item(item_id)["is_available"])
    attempt(action, "Dish availability changed.")
    return redirect(url_for("menu.manage"))


@bp.post("/item/<int:item_id>/delete")
@role_required("Manager")
def item_delete(item_id):
    attempt(lambda: MenuService().delete_item(item_id), "Dish deleted.")
    return redirect(url_for("menu.manage"))


# ----- categories ('Manage categories' button) -----
@bp.route("/categories")
@role_required("Manager")
def categories():
    return render_template("menu/categories.html", categories=MenuService().list_categories())


@bp.post("/category/new")
@role_required("Manager")
def category_new():
    attempt(lambda: MenuService().create_category(request.form.get("name")), "Category added.")
    return redirect(url_for("menu.categories"))


@bp.post("/category/<int:category_id>/rename")
@role_required("Manager")
def category_rename(category_id):
    attempt(lambda: MenuService().rename_category(category_id, request.form.get("name")),
            "Category renamed.")
    return redirect(url_for("menu.categories"))


@bp.post("/category/<int:category_id>/delete")
@role_required("Manager")
def category_delete(category_id):
    attempt(lambda: MenuService().delete_category(category_id), "Category deleted.")
    return redirect(url_for("menu.categories"))
