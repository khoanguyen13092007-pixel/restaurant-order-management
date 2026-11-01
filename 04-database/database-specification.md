# NV4 – Mô tả cấu trúc cơ sở dữ liệu

Hệ quản trị: **MySQL 8**. Cơ sở dữ liệu gồm **18 bảng** (16 thực thể + 2 bảng trung gian, xem mục 4), ánh xạ từ class diagram của NV3 (`ClassDiagram_SE_DVK.drawio.xml`). Script tạo bảng: [`appendix/schema.sql`](appendix/schema.sql). Sơ đồ ERD (draw.io): [`erd.drawio`](erd.drawio) – trang 1 vẽ theo mô hình thực thể – kết hợp (bản số min,max), trang 2 là lược đồ quan hệ có khóa ngoại.

**Ký hiệu:** PK = khóa chính · FK = khóa ngoại · UQ = giá trị duy nhất · NN = NOT NULL. Tiền lưu bằng `DECIMAL(12,2)` (VNĐ) để không sai số làm tròn.

## 1. Quy ước đặt tên

- Tên bảng: tiếng Anh, chữ thường, `snake_case`, số nhiều của tên class (`Order` → `orders`, `MenuCategory` → `menu_categories`).
- Tên cột: `snake_case` của thuộc tính class (`createdByAccountId` → `created_by_account_id`).
- Khóa chính: `INT AUTO_INCREMENT` (riêng `sessions.session_id` là chuỗi token ngẫu nhiên).
- Giá trị trạng thái: `ENUM` viết hoa, dùng đúng giá trị NV3 đề xuất trong ghi chú class diagram.

## 2. Ánh xạ class → bảng

| Class (NV3) | Bảng | FR / NFR |
| --- | --- | --- |
| Permission | `permissions` | FR-13 |
| Role | `roles` | FR-13 |
| (quan hệ Role – Permission, N–N) | `role_permissions` | FR-13 |
| User, Waiter, Chef, Cashier, Manager | `accounts` (phân biệt bằng `role_id`) | FR-13 |
| Session | `sessions` | NFR bảo mật (hết hạn phiên) |
| AuditLog | `audit_logs` | NFR bảo mật |
| Customer | `customers` | FR-05 |
| Discount | `discounts` | FR-10 |
| MenuCategory | `menu_categories` | FR-01, FR-02 |
| MenuItem | `menu_items` | FR-01, FR-02 |
| RestaurantTable | `restaurant_tables` | FR-03 |
| Order | `orders` | FR-04, FR-05, FR-10 |
| OrderTable | `order_tables` | FR-04 |
| KitchenTicket | `kitchen_tickets` | FR-07, FR-08 |
| OrderItem | `order_items` | FR-05, FR-06, FR-08 |
| Notification | `notifications` | FR-09 |
| Payment | `payments` | FR-11, FR-12 |
| Invoice | `invoices` | FR-11 |
| «service» ReportService | không có bảng – truy vấn trên `payments`, `order_items` | FR-12 |

Waiter, Chef, Cashier, Manager kế thừa User và chỉ khác nhau ở phương thức, không khác thuộc tính, nên dùng **một bảng** `accounts` (single-table inheritance) như ghi chú của NV3.

## 3. Mô tả từng bảng

### 3.1. permissions – Quyền

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| permission_id | INT | PK | AUTO_INCREMENT | Mã quyền |
| code | VARCHAR(50) | UQ | NN | Mã quyền, ví dụ `MENU_EDIT`, `REPORT_VIEW` |
| description | VARCHAR(255) | | | Mô tả |

### 3.2. roles – Vai trò

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| role_id | INT | PK | AUTO_INCREMENT | Mã vai trò |
| code | VARCHAR(30) | UQ | NN | `WAITER`, `CHEF`, `CASHIER`, `MANAGER` |
| name | VARCHAR(100) | | NN | Tên hiển thị (Nhân viên phục vụ, Bếp, Thu ngân, Quản lý) |

### 3.3. role_permissions – Vai trò có quyền nào

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| role_id | INT | PK, FK → roles | NN | Vai trò |
| permission_id | INT | PK, FK → permissions | NN | Quyền |

Bảng trung gian cho quan hệ nhiều–nhiều Role – Permission.

### 3.4. accounts – Tài khoản nhân viên (class User)

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| account_id | INT | PK | AUTO_INCREMENT | Mã tài khoản |
| role_id | INT | FK → roles | NN | Vai trò, quyết định là Waiter/Chef/Cashier/Manager |
| username | VARCHAR(50) | UQ | NN | Tên đăng nhập |
| password_hash | VARCHAR(255) | | NN | Mật khẩu đã băm (bcrypt), không lưu mật khẩu gốc |
| full_name | VARCHAR(100) | | NN | Họ tên |
| status | ENUM | | NN, mặc định `ACTIVE` | `ACTIVE` = đang dùng, `LOCKED` = bị khóa (nghỉ việc) |
| created_at | DATETIME | | NN, mặc định NOW | Ngày tạo |

### 3.5. sessions – Phiên đăng nhập

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| session_id | VARCHAR(64) | PK | | Token ngẫu nhiên |
| account_id | INT | FK → accounts | NN | Ai đăng nhập |
| last_active_at | DATETIME | | NN | Lần thao tác cuối |
| expires_at | DATETIME | | NN | Hết hạn; mỗi thao tác gia hạn (`refresh()`), quá hạn thì `isExpired()` = true |

### 3.6. audit_logs – Nhật ký thao tác

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| log_id | BIGINT | PK | AUTO_INCREMENT | Mã nhật ký (BIGINT vì bảng tăng nhanh) |
| account_id | INT | FK → accounts | NN | Ai thực hiện |
| action | VARCHAR(255) | | NN | Hành động, ví dụ "Hủy món #120" |
| created_at | DATETIME | | NN, mặc định NOW | Thời điểm |

### 3.7. customers – Khách hàng

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| customer_id | INT | PK | AUTO_INCREMENT | Mã khách |
| full_name | VARCHAR(100) | | NULL | Tên khách (không bắt buộc) |
| phone | VARCHAR(15) | | NULL | Số điện thoại (không bắt buộc) |

Khách không có tài khoản đăng nhập; tích điểm nằm ngoài phạm vi.

### 3.8. discounts – Mã giảm giá

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| discount_id | INT | PK | AUTO_INCREMENT | Mã |
| code | VARCHAR(30) | UQ | NN | Mã nhập khi thanh toán |
| type | ENUM | | NN | `PERCENT` = giảm theo %, `FIXED` = giảm số tiền cố định |
| value | DECIMAL(12,2) | | NN, CHECK > 0 | Giá trị giảm |

### 3.9. menu_categories – Danh mục món

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| category_id | INT | PK | AUTO_INCREMENT | Mã danh mục |
| name | VARCHAR(100) | UQ | NN | Tên danh mục (Khai vị, Món chính, Đồ uống…) |

### 3.10. menu_items – Món ăn

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| item_id | INT | PK | AUTO_INCREMENT | Mã món |
| category_id | INT | FK → menu_categories | NN | Danh mục (FR-02 lọc theo cột này) |
| name | VARCHAR(150) | | NN | Tên món |
| description | TEXT | | NULL | Mô tả |
| price | DECIMAL(12,2) | | NN, CHECK ≥ 0 | Giá hiện tại |
| status | ENUM | | NN, mặc định `AVAILABLE` | `AVAILABLE` = còn, `SOLD_OUT` = hết, `DELETED` = đã xóa (xóa mềm) |

### 3.11. restaurant_tables – Bàn

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| table_id | INT | PK | AUTO_INCREMENT | Mã bàn |
| code | VARCHAR(10) | UQ | NN | Số bàn hiển thị (T01…) |
| status | ENUM | | NN, mặc định `AVAILABLE` | `AVAILABLE` = trống, `OCCUPIED` = đang dùng, `RESERVED` = đã đặt (FR-03) |

### 3.12. orders – Đơn gọi món

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| order_id | INT | PK | AUTO_INCREMENT | Mã đơn |
| customer_id | INT | FK → customers | NULL | Có giá trị khi khách tự gọi món |
| created_by_account_id | INT | FK → accounts | NULL | Có giá trị khi nhân viên phục vụ tạo đơn |
| discount_id | INT | FK → discounts | NULL | Mã giảm giá đã áp dụng |
| idempotency_key | VARCHAR(64) | UQ | NN | Mã do máy tạo đơn sinh ra; gửi lại cùng mã không tạo đơn trùng |
| status | ENUM | | NN, mặc định `DRAFT` | `DRAFT` → `CONFIRMED` → `PAID`, hoặc `CANCELLED` |
| note | VARCHAR(255) | | NULL | Ghi chú chung |
| subtotal | DECIMAL(12,2) | | NN, mặc định 0 | Tổng tiền món (không tính món đã hủy) |
| discount_amount | DECIMAL(12,2) | | NN, mặc định 0 | Tiền giảm |
| tax_amount | DECIMAL(12,2) | | NN, mặc định 0 | Tiền thuế |
| total_amount | DECIMAL(12,2) | | NN, CHECK = subtotal − discount + tax | Số tiền phải trả |
| created_at | DATETIME | | NN, mặc định NOW | Giờ tạo đơn |

### 3.13. order_tables – Đơn và bàn

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| order_id | INT | PK, FK → orders | NN | Đơn |
| table_id | INT | PK, FK → restaurant_tables | NN | Bàn |
| is_primary | BOOLEAN | | NN, mặc định FALSE | Bàn chính khi gộp nhiều bàn |

Gộp bàn: thêm dòng cùng `order_id`. Chuyển bàn: đổi `table_id`.

### 3.14. kitchen_tickets – Phiếu bếp

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| ticket_id | INT | PK | AUTO_INCREMENT | Mã phiếu |
| order_id | INT | FK → orders | NN | Thuộc đơn nào |
| status | ENUM | | NN, mặc định `SENT` | `SENT` = đã gửi, `IN_PROGRESS` = bếp đang làm, `COMPLETED` = xong hết món |
| created_at | DATETIME | | NN, mặc định NOW | Giờ gửi bếp; bếp làm phiếu cũ trước |

Mỗi lần xác nhận (`Order.confirm()`) tạo một phiếu chứa các món mới thêm, nên khách gọi thêm món sẽ có phiếu thứ hai.

### 3.15. order_items – Món trong đơn

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| order_item_id | INT | PK | AUTO_INCREMENT | Mã dòng món |
| order_id | INT | FK → orders | NN | Thuộc đơn nào |
| menu_item_id | INT | FK → menu_items | NN | Món nào |
| ticket_id | INT | FK → kitchen_tickets | NULL | NULL = chưa gửi bếp |
| quantity | INT | | NN, CHECK > 0 | Số lượng |
| unit_price | DECIMAL(12,2) | | NN | Giá tại lúc gọi (giữ đúng hóa đơn khi giá món thay đổi) |
| note | VARCHAR(255) | | NULL | Ghi chú (ít cay…) |
| status | ENUM | | NN, mặc định `PENDING` | `PENDING` → `RECEIVED` → `COOKING` → `DONE`, hoặc `CANCELLED` |

FR-06: `canModify()` trả về true khi `status` là `PENDING` hoặc `RECEIVED` (bếp chưa chế biến).

### 3.16. notifications – Thông báo

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| notification_id | INT | PK | AUTO_INCREMENT | Mã thông báo |
| recipient_account_id | INT | FK → accounts | NN | Nhân viên nhận |
| related_order_item_id | INT | FK → order_items | NN | Món vừa xong |
| is_read | BOOLEAN | | NN, mặc định FALSE | Đã đọc chưa |
| created_at | DATETIME | | NN, mặc định NOW | Thời điểm |

Tạo khi một món chuyển sang `DONE` (FR-09).

### 3.17. payments – Thanh toán

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| payment_id | INT | PK | AUTO_INCREMENT | Mã thanh toán |
| order_id | INT | FK → orders | NN | Đơn được thanh toán |
| cashier_account_id | INT | FK → accounts | NN | Thu ngân thực hiện |
| amount | DECIMAL(12,2) | | NN, CHECK > 0 | Số tiền |
| method | ENUM | | NN | `CASH`, `CARD`, `TRANSFER` |
| status | ENUM | | NN, mặc định `PENDING` | `PENDING` = đang xử lý, `SUCCESS` = thành công, `FAILED` = thất bại |
| paid_at | DATETIME | | NULL | Thời điểm thành công; báo cáo doanh thu lọc theo cột này |

Một đơn có thể có nhiều lần thanh toán (ví dụ lần quẹt thẻ đầu thất bại), đúng bản số 1–0..N của NV3.

### 3.18. invoices – Hóa đơn

| Cột | Kiểu | Khóa | Ràng buộc | Mô tả |
| --- | --- | --- | --- | --- |
| invoice_id | INT | PK | AUTO_INCREMENT | Mã hóa đơn |
| order_id | INT | FK → orders, UQ | NN | Mỗi đơn tối đa một hóa đơn |
| invoice_number | VARCHAR(20) | UQ | NN | Số hóa đơn in ra |
| issued_at | DATETIME | | NN, mặc định NOW | Giờ xuất |

## 4. Mối kết hợp và bản số

Bảng dưới khớp đúng trang 1 của `erd.drawio`. Bản số (min,max) ghi cạnh thực thể nào thì cho biết một thể hiện của thực thể đó tham gia mối kết hợp ít nhất / nhiều nhất mấy lần. Ví dụ ROLE (0,n) – grants – (1,1) ACCOUNT: một vai trò có 0..n tài khoản, mỗi tài khoản có đúng 1 vai trò.

| Mối kết hợp (tên NV3) | Thực thể A (min,max) | Thực thể B (min,max) | Cài đặt trong CSDL |
| --- | --- | --- | --- |
| grants | ROLE (0,n) | ACCOUNT (1,1) | FK `accounts.role_id` |
| has | ROLE (0,n) | PERMISSION (0,n) | Bảng trung gian `role_permissions` |
| opens | ACCOUNT (0,n) | SESSION (1,1) | FK `sessions.account_id` |
| writes | ACCOUNT (0,n) | AUDIT_LOG (1,1) | FK `audit_logs.account_id` |
| creates | ACCOUNT (0,n) | ORDER (0,1) | FK `orders.created_by_account_id` (NULL được) |
| places | CUSTOMER (0,n) | ORDER (0,1) | FK `orders.customer_id` (NULL được) |
| applies | DISCOUNT (0,n) | ORDER (0,1) | FK `orders.discount_id` (NULL được) |
| contains | MENU_CATEGORY (0,n) | MENU_ITEM (1,1) | FK `menu_items.category_id` |
| referenced_by | MENU_ITEM (0,n) | ORDER_ITEM (1,1) | FK `order_items.menu_item_id` |
| contains | ORDER (1,n) | ORDER_ITEM (1,1) | FK `order_items.order_id` |
| uses (thuộc tính `is_primary`) | ORDER (0,n) | RESTAURANT_TABLE (0,n) | Bảng trung gian `order_tables` |
| sends | ORDER (0,n) | KITCHEN_TICKET (1,1) | FK `kitchen_tickets.order_id` |
| groups | KITCHEN_TICKET (1,n) | ORDER_ITEM (0,1) | FK `order_items.ticket_id` (NULL được) |
| triggers | ORDER_ITEM (0,n) | NOTIFICATION (1,1) | FK `notifications.related_order_item_id` |
| receives | ACCOUNT (0,n) | NOTIFICATION (1,1) | FK `notifications.recipient_account_id` |
| paid_by | ORDER (0,n) | PAYMENT (1,1) | FK `payments.order_id` |
| processes | ACCOUNT (0,n) | PAYMENT (1,1) | FK `payments.cashier_account_id` |
| issued | ORDER (0,1) | INVOICE (1,1) | FK `invoices.order_id` (UQ) |

**Vì sao ERD có 16 thực thể mà CSDL có 18 bảng:** hai mối kết hợp nhiều–nhiều `has` (ROLE – PERMISSION) và `uses` (ORDER – RESTAURANT_TABLE) không thành thực thể trên ERD. Khi chuyển sang bảng, mỗi mối kết hợp này tách thành một bảng trung gian (`role_permissions`, `order_tables`), nên có 16 + 2 = 18 bảng. Các mối kết hợp 1–n chỉ cần một khóa ngoại ở bảng phía (1,1) hoặc (0,1).

Bản số (1,n) của ORDER trong `contains` (đơn phải có ít nhất 1 món) không ép được bằng khóa ngoại; ứng dụng kiểm tra trước khi cho xác nhận đơn.

## 5. Chuẩn hóa và đáp ứng NFR

- **1NF:** mọi bảng có khóa chính, mỗi ô một giá trị; danh sách món của đơn nằm ở `order_items`, không gom vào một cột.
- **2NF:** hai bảng khóa ghép (`order_tables`, `role_permissions`) không có cột nào chỉ phụ thuộc một phần khóa.
- **3NF:** không phụ thuộc bắc cầu; ví dụ tên vai trò chỉ ở `roles`, tên danh mục chỉ ở `menu_categories`.
- **Ngoại lệ có chủ ý:** `order_items.unit_price` và các cột tiền trong `orders` là số liệu chốt tại một thời điểm (giá lúc bán, tổng lúc tính tiền), giữ theo thiết kế của NV3 để hóa đơn không đổi khi giá món đổi. Ràng buộc CHECK giữ `total_amount` luôn khớp công thức.

| NFR | Cách CSDL đáp ứng |
| --- | --- |
| Bảo mật – mật khẩu mã hóa | `accounts.password_hash` (bcrypt) |
| Bảo mật – phân quyền theo vai trò | `roles`, `permissions`, `role_permissions` |
| Bảo mật – phiên hết hạn | `sessions.expires_at`, `last_active_at` |
| Toàn vẹn – tránh trùng đơn | `orders.idempotency_key` UNIQUE |
| Toàn vẹn – dữ liệu lịch sử | xóa mềm món (`status = DELETED`), khóa tài khoản (`LOCKED`) thay vì xóa |
| Hiệu năng | index cho hàng đợi bếp, hộp thư thông báo, báo cáo doanh thu |
| Độ tin cậy – sao lưu hằng ngày | thực hiện bằng `mysqldump` theo lịch, ngoài phạm vi thiết kế bảng |
