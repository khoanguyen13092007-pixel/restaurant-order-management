-- =====================================================================
-- Report queries for FR-12 (used by ReportService)
-- Revenue = sum of SUCCESS payments, grouped by the time they were paid.
-- =====================================================================
USE restaurant_order_management;

-- 1. Revenue by day (example: November 2026)
SELECT DATE(paid_at)        AS report_date,
       COUNT(DISTINCT order_id) AS paid_orders,
       SUM(amount)          AS revenue
FROM payments
WHERE status = 'SUCCESS'
  AND paid_at >= '2026-11-01' AND paid_at < '2026-12-01'
GROUP BY DATE(paid_at)
ORDER BY report_date;

-- 2. Revenue by ISO week
SELECT YEARWEEK(paid_at, 3) AS report_week,
       SUM(amount)          AS revenue
FROM payments
WHERE status = 'SUCCESS'
GROUP BY YEARWEEK(paid_at, 3)
ORDER BY report_week;

-- 3. Revenue by month
SELECT DATE_FORMAT(paid_at, '%Y-%m') AS report_month,
       SUM(amount)                   AS revenue
FROM payments
WHERE status = 'SUCCESS'
GROUP BY DATE_FORMAT(paid_at, '%Y-%m')
ORDER BY report_month;

-- 4. Top 10 best-selling items in a period
SELECT mi.item_id,
       mi.name,
       SUM(oi.quantity)                 AS quantity_sold,
       SUM(oi.quantity * oi.unit_price) AS item_revenue
FROM order_items oi
JOIN orders     o  ON o.order_id = oi.order_id
JOIN menu_items mi ON mi.item_id = oi.menu_item_id
WHERE o.status = 'PAID'
  AND oi.status <> 'CANCELLED'
  AND o.created_at >= '2026-11-01' AND o.created_at < '2026-12-01'
GROUP BY mi.item_id, mi.name
ORDER BY quantity_sold DESC
LIMIT 10;

-- 5. Kitchen queue (FR-08): items waiting or being cooked, oldest ticket first
SELECT kt.ticket_id, kt.created_at, oi.order_item_id, mi.name,
       oi.quantity, oi.note, oi.status
FROM order_items oi
JOIN kitchen_tickets kt ON kt.ticket_id = oi.ticket_id
JOIN menu_items      mi ON mi.item_id   = oi.menu_item_id
WHERE oi.status IN ('PENDING','RECEIVED','COOKING')
ORDER BY kt.created_at, oi.order_item_id;
