"""Kết nối SQLite và tạo 10 bảng theo ERD (mục 6.3 của đặc tả)."""
import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS "CUSTOMER" (
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT NOT NULL,
    phone       TEXT
);
CREATE TABLE IF NOT EXISTS "USER" (
    user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name     TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active','inactive')),
    role          TEXT NOT NULL CHECK (role IN ('Waitstaff','Kitchen','Cashier','Manager'))
);
CREATE TABLE IF NOT EXISTS "MENU_CATEGORY" (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS "MENU_ITEM" (
    menu_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id  INTEGER NOT NULL REFERENCES "MENU_CATEGORY"(category_id),
    name         TEXT NOT NULL,
    description  TEXT,
    price        REAL NOT NULL CHECK (price >= 0),
    is_available INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS "RESTAURANT_TABLE" (
    table_id INTEGER PRIMARY KEY AUTOINCREMENT,
    code     TEXT NOT NULL UNIQUE,
    status   TEXT NOT NULL DEFAULT 'available'
);
CREATE TABLE IF NOT EXISTS "ORDER" (
    order_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER REFERENCES "CUSTOMER"(customer_id),
    waitstaff_id    INTEGER REFERENCES "USER"(user_id),
    status          TEXT NOT NULL DEFAULT 'draft',
    note            TEXT,
    subtotal        REAL NOT NULL DEFAULT 0,
    discount_amount REAL NOT NULL DEFAULT 0,
    tax_amount      REAL NOT NULL DEFAULT 0,
    total_amount    REAL NOT NULL DEFAULT 0,
    created_at      TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "ORDER_TABLE" (
    order_id INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    table_id INTEGER NOT NULL REFERENCES "RESTAURANT_TABLE"(table_id),
    PRIMARY KEY (order_id, table_id)
);
CREATE TABLE IF NOT EXISTS "KITCHEN_TICKET" (
    ticket_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    status     TEXT NOT NULL DEFAULT 'received',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS "ORDER_ITEM" (
    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    menu_item_id  INTEGER NOT NULL REFERENCES "MENU_ITEM"(menu_item_id),
    ticket_id     INTEGER REFERENCES "KITCHEN_TICKET"(ticket_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    REAL NOT NULL,
    note          TEXT,
    status        TEXT NOT NULL DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS "PAYMENT" (
    payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL REFERENCES "ORDER"(order_id),
    cashier_id INTEGER NOT NULL REFERENCES "USER"(user_id),
    amount     REAL NOT NULL,
    method     TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'paid',
    paid_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_order_item_order ON "ORDER_ITEM"(order_id);
CREATE INDEX IF NOT EXISTS idx_order_created ON "ORDER"(created_at);
CREATE INDEX IF NOT EXISTS idx_payment_paid_at ON "PAYMENT"(paid_at);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.executescript(SCHEMA)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
