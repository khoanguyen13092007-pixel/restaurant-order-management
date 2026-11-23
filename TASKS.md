# Phân công nhiệm vụ - Nhóm 10

> **Trạng thái:** bản đầu của cả 5 module đã được code sẵn và có test (xem `docs/test_case_index.md`).
> Mỗi người đọc kỹ, chạy thử và hiểu module của mình, sửa lỗi, bổ sung chức năng còn thiếu theo đặc tả,
> và tự viết thêm test. Đừng nộp những phần mình chưa hiểu: cô có thể hỏi về code của từng người.

Mỗi người phụ trách trọn một module: model, repository, service, controller, template, unit test
và phần test case trong Testing Document. Tên lớp, thuộc tính, phương thức phải đúng class diagram
(mục V của đặc tả). Chỉ sửa file thuộc module của mình; muốn sửa file người khác thì báo họ.

| NV | Module | FR / Use case | File chính |
|----|--------|---------------|------------|
| 1 | Nền tảng và Xác thực | FR-14, UC Login/Logout | `models/user.py`, `services/auth_service.py`, `controllers/auth_controller.py`, `utils/`, `database.py`, `base.html`, `templates/auth/`, `Dockerfile`, `tests/test_auth.py` |
| 2 | Thực đơn và Bàn | FR-01..04, UC Manage Menu, View/Search Menu, View Table Status, Assign/Move/Merge Tables | `models/menu.py`, `repositories/menu_repository.py`, `services/menu_service.py`, `controllers/menu_controller.py`, `templates/menu/`, `tests/test_menu_tables.py` |
| 3 | Đơn hàng | FR-05..07, UC Create and Confirm Order, Edit or Cancel Item | `models/order.py`, `repositories/order_repository.py`, `services/order_service.py`, `controllers/order_controller.py`, `templates/orders/`, `tests/test_orders.py` |
| 4 | Bếp, thông báo, Tài liệu kiểm thử | FR-08..10, UC View Items to Prepare, Update Item Status, Receive Ready Notification | `models/kitchen.py`, `repositories/kitchen_repository.py`, `services/kitchen_service.py`, `controllers/kitchen_controller.py`, `templates/kitchen/`, `tests/test_kitchen.py`, `docs/Testing_Document` |
| 5 | Thanh toán và Báo cáo | FR-11..13, UC Calculate Total/Discount/Tax, Process Payment and Print Invoice, View Revenue and Best-Selling | `models/payment.py`, `repositories/payment_repository.py`, `services/payment_service.py`, `controllers/payment_controller.py`, `templates/payment/`, `tests/test_payment_reports.py` |

Các file dùng chung ngoài bảng trên: `services/pricing.py` (tính tiền, NV5 viết, NV3 gọi),
`services/table_service.py` + `repositories/table_repository.py` + `controllers/table_controller.py` (NV2),
`controllers/customer_controller.py` + `templates/customer/` (khách tự gọi món, NV3), `static/css/style.css` (giao diện chung, NV1), `utils/web.py` (NV1).

## Màn hình theo thiết kế GUI (mục VII của đặc tả)

| Màn hình | Route | Template | Người phụ trách |
|---|---|---|---|
| Staff login | `/login` | `auth/login.html` | NV1 |
| Menu & Orders (khách, phục vụ) | `/customer/<bàn>`, `/orders/new` | `orders/menu_order.html`, `static/js/order.js` | NV3 (menu: NV2) |
| Tables & Orders | `/tables/` | `tables/screen.html` | NV2 (bàn), NV3 (đơn), NV4 (thông báo món xong) |
| Kitchen | `/kitchen/` | `kitchen/board.html` | NV4 |
| Cashier | `/payment/` | `payment/payment.html`, `payment/invoice.html` | NV5 |
| Manager - Menu items | `/menu/manage` | `menu/manage.html`, `menu/categories.html` | NV2 |
| Manager - Tables | `/tables/manage` | `tables/manage.html` | NV2 |
| Manager - Reports | `/payment/reports` | `payment/reports.html` | NV5 |

## Phụ thuộc
- NV1 xong khung, CSDL, đăng nhập, `seed.py` trước (đã có sẵn bản đầu trong repo này).
- NV3 cần dữ liệu của NV2; NV4 và NV5 cần đơn hàng của NV3. Trong lúc chờ, dùng dữ liệu `seed.py`.

## Quy ước làm việc
- Không push thẳng vào `main`. Mỗi tính năng một nhánh `feature/<module>-<tên>`, gộp qua pull request có ít nhất 1 người duyệt.
- CI (GitHub Actions) tự chạy test cho mỗi pull request; test đỏ thì chưa gộp.
- Tên test dạng `test_TC_<MODULE>_<số>_...` (ví dụ `TC_AUTH_01`), cùng mã với test case trong Testing Document.
- Testing Document: dùng đúng template tải từ Elearning mục 5, không đổi bố cục. NV4 kiểm tra lần cuối.
