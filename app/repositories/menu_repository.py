from app.database import get_db
from app.repositories.base_repository import BaseRepository


class MenuCategoryRepository(BaseRepository):  # NV2
    table = "MENU_CATEGORY"
    pk = "category_id"

    def get_all(self):
        return get_db().execute('SELECT * FROM "MENU_CATEGORY" ORDER BY category_id').fetchall()

    def count_items(self, category_id):
        return get_db().execute(
            'SELECT COUNT(*) FROM "MENU_ITEM" WHERE category_id = ?', (category_id,)
        ).fetchone()[0]


class MenuItemRepository(BaseRepository):  # NV2
    table = "MENU_ITEM"
    pk = "menu_item_id"

    def list_with_category(self):
        return get_db().execute(
            """SELECT mi.*, mc.name AS category_name
               FROM "MENU_ITEM" mi JOIN "MENU_CATEGORY" mc ON mc.category_id = mi.category_id
               ORDER BY mi.menu_item_id"""
        ).fetchall()

    def is_referenced(self, menu_item_id):
        return get_db().execute(
            'SELECT COUNT(*) FROM "ORDER_ITEM" WHERE menu_item_id = ?', (menu_item_id,)
        ).fetchone()[0] > 0
