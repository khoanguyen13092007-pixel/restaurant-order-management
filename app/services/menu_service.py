"""NV2 - Menu business logic (FR-01, FR-02)."""
import math
import unicodedata

from app.repositories.menu_repository import MenuCategoryRepository, MenuItemRepository
from app.services.errors import ServiceError


def normalize(text):
    """Case- and accent-insensitive text for searching (so 'pho' finds 'Phở')."""
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn").casefold().strip()


def parse_price(value):
    try:
        price = float(str(value).replace(",", "").strip())
    except ValueError:
        raise ServiceError("Price is not a valid number.")
    if not math.isfinite(price) or price < 0:
        raise ServiceError("Price must be zero or more.")
    return price


def _clean_name(name, what):
    name = (name or "").strip()
    if not name:
        raise ServiceError(f"The {what} name cannot be empty.")
    if len(name) > 100:
        raise ServiceError(f"The {what} name is too long (maximum 100 characters).")
    return name


class MenuService:
    def __init__(self):
        self.categories = MenuCategoryRepository()
        self.items = MenuItemRepository()

    # ----- categories -----
    def list_categories(self):
        return self.categories.get_all()

    def create_category(self, name):
        return self.categories.add({"name": _clean_name(name, "category")})

    def rename_category(self, category_id, name):
        self._category(category_id)
        self.categories.update(category_id, {"name": _clean_name(name, "category")})

    def delete_category(self, category_id):
        self._category(category_id)
        if self.categories.count_items(category_id):
            raise ServiceError("This category still has dishes. Move or delete them first.")
        self.categories.delete(category_id)

    def _category(self, category_id):
        row = self.categories.get_by_id(category_id)
        if row is None:
            raise ServiceError("Category not found.")
        return row

    # ----- dishes -----
    def get_item(self, menu_item_id):
        row = self.items.get_by_id(menu_item_id)
        if row is None:
            raise ServiceError("Dish not found.")
        return row

    def search_items(self, keyword="", category_id=None, only_available=False):
        """FR-02: view and search the menu by name, description or category."""
        key = normalize(keyword)
        result = []
        for row in self.items.list_with_category():
            if only_available and not row["is_available"]:
                continue
            if category_id and row["category_id"] != category_id:
                continue
            if key and key not in normalize(row["name"]) and key not in normalize(row["description"]):
                continue
            result.append(row)
        return result

    def create_item(self, category_id, name, description, price, is_available=True):
        self._category(category_id)
        return self.items.add({
            "category_id": category_id,
            "name": _clean_name(name, "dish"),
            "description": (description or "").strip()[:300] or None,
            "price": parse_price(price),
            "is_available": 1 if is_available else 0,
        })

    def update_item(self, menu_item_id, category_id, name, description, price, is_available=None):
        self.get_item(menu_item_id)
        self._category(category_id)
        changes = {
            "category_id": category_id,
            "name": _clean_name(name, "dish"),
            "description": (description or "").strip()[:300] or None,
            "price": parse_price(price),
        }
        if is_available is not None:
            changes["is_available"] = 1 if is_available else 0
        self.items.update(menu_item_id, changes)

    def set_available(self, menu_item_id, value):
        self.get_item(menu_item_id)
        self.items.update(menu_item_id, {"is_available": 1 if value else 0})

    def update_price(self, menu_item_id, price):
        self.get_item(menu_item_id)
        self.items.update(menu_item_id, {"price": parse_price(price)})

    def delete_item(self, menu_item_id):
        self.get_item(menu_item_id)
        if self.items.is_referenced(menu_item_id):
            raise ServiceError("This dish appears in orders and cannot be deleted. Mark it as sold out instead.")
        self.items.delete(menu_item_id)
        
