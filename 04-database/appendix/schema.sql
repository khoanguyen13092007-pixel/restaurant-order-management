-- =====================================================================
-- Restaurant Order Management System - Database schema (NV4)
-- DBMS: MySQL 8.0+
-- Based on: ClassDiagram_SE_DVK.drawio.xml (NV3)
-- Tables are created in dependency order (referenced tables first).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS restaurant_order_management
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE restaurant_order_management;

-- ---------------------------------------------------------------------
-- 1. Accounts & authorization (FR-13, NFR security)
-- ---------------------------------------------------------------------

-- Class: Permission
CREATE TABLE permissions (
  permission_id INT AUTO_INCREMENT PRIMARY KEY,
  code          VARCHAR(50)  NOT NULL UNIQUE,
  description   VARCHAR(255)
);

-- Class: Role  (code: WAITER, CHEF, CASHIER, MANAGER)
CREATE TABLE roles (
  role_id INT AUTO_INCREMENT PRIMARY KEY,
  code    VARCHAR(30)  NOT NULL UNIQUE,
  name    VARCHAR(100) NOT NULL
);

-- Junction table for Role "has" Permission (N-N)
CREATE TABLE role_permissions (
  role_id       INT NOT NULL,
  permission_id INT NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  FOREIGN KEY (role_id)       REFERENCES roles(role_id),
  FOREIGN KEY (permission_id) REFERENCES permissions(permission_id)
);

-- Class: User (abstract) + Waiter / Chef / Cashier / Manager
-- Single-table inheritance: subclasses are distinguished by role_id.
CREATE TABLE accounts (
  account_id    INT AUTO_INCREMENT PRIMARY KEY,
  role_id       INT          NOT NULL,
  username      VARCHAR(50)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,            -- bcrypt hash, never plain text
  full_name     VARCHAR(100) NOT NULL,
  status        ENUM('ACTIVE','LOCKED') NOT NULL DEFAULT 'ACTIVE',
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- Class: Session  (NFR: session expires after inactivity)
CREATE TABLE sessions (
  session_id     VARCHAR(64) PRIMARY KEY,          -- random token
  account_id     INT      NOT NULL,
  last_active_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at     DATETIME NOT NULL,
  FOREIGN KEY (account_id) REFERENCES accounts(account_id),
  INDEX idx_sessions_account (account_id)
);

-- Class: AuditLog
CREATE TABLE audit_logs (
  log_id     BIGINT AUTO_INCREMENT PRIMARY KEY,
  account_id INT          NOT NULL,
  action     VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (account_id) REFERENCES accounts(account_id),
  INDEX idx_audit_created (created_at)
);

-- ---------------------------------------------------------------------
-- 2. Customers & discounts
-- ---------------------------------------------------------------------

-- Class: Customer  (no login; loyalty points are out of scope)
CREATE TABLE customers (
  customer_id INT AUTO_INCREMENT PRIMARY KEY,
  full_name   VARCHAR(100),
  phone       VARCHAR(15)
);

-- Class: Discount  (FR-10)
CREATE TABLE discounts (
  discount_id INT AUTO_INCREMENT PRIMARY KEY,
  code        VARCHAR(30) NOT NULL UNIQUE,
  type        ENUM('PERCENT','FIXED') NOT NULL,
  value       DECIMAL(12,2) NOT NULL CHECK (value > 0)
);

-- ---------------------------------------------------------------------
-- 3. Menu (FR-01, FR-02)
-- ---------------------------------------------------------------------

-- Class: MenuCategory
CREATE TABLE menu_categories (
  category_id INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(100) NOT NULL UNIQUE
);

-- Class: MenuItem  (status DELETED = soft delete, keeps order history)
CREATE TABLE menu_items (
  item_id     INT AUTO_INCREMENT PRIMARY KEY,
  category_id INT           NOT NULL,
  name        VARCHAR(150)  NOT NULL,
  description TEXT,
  price       DECIMAL(12,2) NOT NULL CHECK (price >= 0),
  status      ENUM('AVAILABLE','SOLD_OUT','DELETED') NOT NULL DEFAULT 'AVAILABLE',
  FOREIGN KEY (category_id) REFERENCES menu_categories(category_id),
  INDEX idx_menu_items_category (category_id, status)
);

-- ---------------------------------------------------------------------
-- 4. Tables (FR-03, FR-04)
-- ---------------------------------------------------------------------

-- Class: RestaurantTable
CREATE TABLE restaurant_tables (
  table_id INT AUTO_INCREMENT PRIMARY KEY,
  code     VARCHAR(10) NOT NULL UNIQUE,            -- e.g. T01
  status   ENUM('AVAILABLE','OCCUPIED','RESERVED') NOT NULL DEFAULT 'AVAILABLE'
);

-- ---------------------------------------------------------------------
-- 5. Orders & kitchen (FR-04 .. FR-09)
-- ---------------------------------------------------------------------

-- Class: Order
CREATE TABLE orders (
  order_id              INT AUTO_INCREMENT PRIMARY KEY,
  customer_id           INT NULL,                  -- set when a customer places the order
  created_by_account_id INT NULL,                  -- set when a waiter creates the order
  discount_id           INT NULL,
  idempotency_key       VARCHAR(64) NOT NULL UNIQUE, -- NFR: no duplicate orders on retry
  status                ENUM('DRAFT','CONFIRMED','PAID','CANCELLED') NOT NULL DEFAULT 'DRAFT',
  note                  VARCHAR(255),
  subtotal              DECIMAL(12,2) NOT NULL DEFAULT 0,
  discount_amount       DECIMAL(12,2) NOT NULL DEFAULT 0,
  tax_amount            DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_amount          DECIMAL(12,2) NOT NULL DEFAULT 0,
  created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id)           REFERENCES customers(customer_id),
  FOREIGN KEY (created_by_account_id) REFERENCES accounts(account_id),
  FOREIGN KEY (discount_id)           REFERENCES discounts(discount_id),
  CHECK (total_amount = subtotal - discount_amount + tax_amount),
  INDEX idx_orders_status (status, created_at)
);

-- Class: OrderTable  (merge tables = several rows for one order)
CREATE TABLE order_tables (
  order_id   INT NOT NULL,
  table_id   INT NOT NULL,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (order_id, table_id),
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  FOREIGN KEY (table_id) REFERENCES restaurant_tables(table_id)
);

-- Class: KitchenTicket  (created by Order.confirm(), FR-07)
CREATE TABLE kitchen_tickets (
  ticket_id  INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT NOT NULL,
  status     ENUM('SENT','IN_PROGRESS','COMPLETED') NOT NULL DEFAULT 'SENT',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id),
  INDEX idx_tickets_queue (status, created_at)
);

-- Class: OrderItem
-- ticket_id IS NULL  -> item not sent to the kitchen yet
-- status PENDING / RECEIVED -> can still be edited or cancelled (FR-06)
CREATE TABLE order_items (
  order_item_id INT AUTO_INCREMENT PRIMARY KEY,
  order_id      INT NOT NULL,
  menu_item_id  INT NOT NULL,
  ticket_id     INT NULL,
  quantity      INT NOT NULL CHECK (quantity > 0),
  unit_price    DECIMAL(12,2) NOT NULL,            -- price at order time
  note          VARCHAR(255),
  status        ENUM('PENDING','RECEIVED','COOKING','DONE','CANCELLED') NOT NULL DEFAULT 'PENDING',
  FOREIGN KEY (order_id)     REFERENCES orders(order_id),
  FOREIGN KEY (menu_item_id) REFERENCES menu_items(item_id),
  FOREIGN KEY (ticket_id)    REFERENCES kitchen_tickets(ticket_id),
  INDEX idx_order_items_status (status)
);

-- Class: Notification  (FR-09: waiter is notified when an item is DONE)
CREATE TABLE notifications (
  notification_id       INT AUTO_INCREMENT PRIMARY KEY,
  recipient_account_id  INT NOT NULL,
  related_order_item_id INT NOT NULL,
  is_read               BOOLEAN NOT NULL DEFAULT FALSE,
  created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (recipient_account_id)  REFERENCES accounts(account_id),
  FOREIGN KEY (related_order_item_id) REFERENCES order_items(order_item_id),
  INDEX idx_notifications_inbox (recipient_account_id, is_read)
);

-- ---------------------------------------------------------------------
-- 6. Payment & invoice (FR-10, FR-11)
-- ---------------------------------------------------------------------

-- Class: Payment  (an order may have several payments, e.g. a failed one)
CREATE TABLE payments (
  payment_id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id           INT NOT NULL,
  cashier_account_id INT NOT NULL,
  amount             DECIMAL(12,2) NOT NULL CHECK (amount > 0),
  method             ENUM('CASH','CARD','TRANSFER') NOT NULL,
  status             ENUM('PENDING','SUCCESS','FAILED') NOT NULL DEFAULT 'PENDING',
  paid_at            DATETIME NULL,
  FOREIGN KEY (order_id)           REFERENCES orders(order_id),
  FOREIGN KEY (cashier_account_id) REFERENCES accounts(account_id),
  INDEX idx_payments_report (status, paid_at)
);

-- Class: Invoice  (0..1 per order)
CREATE TABLE invoices (
  invoice_id     INT AUTO_INCREMENT PRIMARY KEY,
  order_id       INT NOT NULL UNIQUE,
  invoice_number VARCHAR(20) NOT NULL UNIQUE,
  issued_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

-- ---------------------------------------------------------------------
-- 7. Seed data for roles
-- ---------------------------------------------------------------------
INSERT INTO roles (code, name) VALUES
  ('MANAGER', 'Quản lý'),
  ('WAITER',  'Nhân viên phục vụ'),
  ('CHEF',    'Bếp'),
  ('CASHIER', 'Thu ngân');
