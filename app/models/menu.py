"""NV2 - MenuCategory, MenuItem, RestaurantTable (class diagram mục 5.2)."""


class MenuCategory:
    def __init__(self, category_id, name):
        self.category_id = category_id
        self.name = name

    @classmethod
    def from_row(cls, row):
        return cls(row["category_id"], row["name"])

    def getItems(self):
        from app.services.menu_service import MenuService
        return MenuService().search_items(category_id=self.category_id)


class MenuItem:
    def __init__(self, menu_item_id, category_id, name, description, price, is_available=True):
        self.menu_item_id = menu_item_id
        self.category_id = category_id
        self.name = name
        self.description = description
        self.price = price
        self.is_available = bool(is_available)

    @classmethod
    def from_row(cls, row):
        return cls(row["menu_item_id"], row["category_id"], row["name"],
                   row["description"], row["price"], row["is_available"])

    def setAvailable(self, value):
        from app.services.menu_service import MenuService
        MenuService().set_available(self.menu_item_id, value)
        self.is_available = bool(value)

    def updatePrice(self, price):
        from app.services.menu_service import MenuService, parse_price
        MenuService().update_price(self.menu_item_id, price)
        self.price = parse_price(price)


class RestaurantTable:
    def __init__(self, table_id, code, status="available"):
        self.table_id = table_id
        self.code = code
        self.status = status

    @classmethod
    def from_row(cls, row):
        return cls(row["table_id"], row["code"], row["status"])

    def occupy(self):
        from app.services.table_service import TableService
        TableService().set_status(self.table_id, "occupied")
        self.status = "occupied"

    def release(self):
        from app.services.table_service import TableService
        TableService().set_status(self.table_id, "available")
        self.status = "available"
