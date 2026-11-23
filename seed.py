"""Create the database and demo data: python seed.py  (safe to run again, no duplicates)."""
from werkzeug.security import generate_password_hash

from app import create_app
from app.database import get_db, init_db

USERS = [
    ("manager", "manager123", "Manager Demo", "Manager", "active"),
    ("waiter", "waiter123", "Waitstaff Demo", "Waitstaff", "active"),
    ("kitchen", "kitchen123", "Kitchen Demo", "Kitchen", "active"),
    ("cashier", "cashier123", "Cashier Demo", "Cashier", "active"),
    ("inactive", "inactive123", "Locked Account", "Waitstaff", "inactive"),
]
CATEGORIES = ["Appetizers", "Main dishes", "Drinks", "Desserts"]
ITEMS = [  # (category, name, description, price, available) - same dishes as the GUI design
    ("Appetizers", "Spring rolls", "Fresh rolls with shrimp and pork", 45000, 1),
    ("Main dishes", "Beef pho", "Rice noodle soup with beef", 65000, 1),
    ("Main dishes", "Grilled chicken", "Grilled chicken with herbs", 120000, 1),
    ("Drinks", "Iced tea", "Iced tea", 20000, 1),
    ("Main dishes", "Fried rice", "Egg fried rice", 55000, 0),   # sold out in the design
    ("Desserts", "Mango pudding", "Mango pudding", 30000, 1),
]
TABLES = ["T%02d" % n for n in range(1, 11)]


def seed():
    db = get_db()
    for username, pwd, full_name, role, status in USERS:
        db.execute(
            'INSERT OR IGNORE INTO "USER" (username, password_hash, full_name, role, status) '
            "VALUES (?,?,?,?,?)",
            (username, generate_password_hash(pwd), full_name, role, status))
    if db.execute('SELECT COUNT(*) FROM "MENU_CATEGORY"').fetchone()[0] == 0:
        for name in CATEGORIES:
            db.execute('INSERT INTO "MENU_CATEGORY" (name) VALUES (?)', (name,))
        for cat, name, desc, price, available in ITEMS:
            cid = db.execute('SELECT category_id FROM "MENU_CATEGORY" WHERE name=?', (cat,)).fetchone()[0]
            db.execute('INSERT INTO "MENU_ITEM" (category_id, name, description, price, is_available) '
                       "VALUES (?,?,?,?,?)", (cid, name, desc, price, available))
    for code in TABLES:
        db.execute('INSERT OR IGNORE INTO "RESTAURANT_TABLE" (code) VALUES (?)', (code,))
    db.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        init_db()
        seed()
    print("Demo data created. Accounts: manager/manager123, waiter/waiter123, "
          "kitchen/kitchen123, cashier/cashier123")
