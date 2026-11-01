# NV4 – Kiểm tra chéo

Đã đối chiếu: `actor, fr và nfr.docx` (yêu cầu), `ClassDiagram_SE_DVK.drawio.xml` (NV3) và CSDL (NV4). Chưa đối chiếu được DFD (NV1) và Use Case (NV2) vì chưa có trong repo.

**Kết quả:** mọi class lưu dữ liệu của NV3 đều có bảng tương ứng, mọi quan hệ có khóa ngoại đúng bản số. Có **10 điểm cần nhóm chốt** (mục 2), phần lớn là giá trị trạng thái NV3 chưa ghi.

## 1. Đối chiếu class (NV3) và bảng (NV4)

| Class | Bảng | Thuộc tính khớp cột | Ghi chú |
| --- | --- | --- | --- |
| Permission | permissions | Đủ | |
| Role | roles | Đủ | |
| – | role_permissions | – | Bảng trung gian cho Role – Permission (N–N), không cần class |
| User (+ Waiter, Chef, Cashier, Manager) | accounts | Đủ | Thêm `created_at` |
| Session | sessions | Đủ | |
| AuditLog | audit_logs | Đủ | |
| Customer | customers | Đủ | |
| Discount | discounts | Đủ | |
| MenuCategory | menu_categories | Đủ | |
| MenuItem | menu_items | Đủ | |
| RestaurantTable | restaurant_tables | Đủ | |
| Order | orders | Đủ | |
| OrderTable | order_tables | Đủ | |
| KitchenTicket | kitchen_tickets | Đủ | |
| OrderItem | order_items | Đủ | |
| Notification | notifications | Đủ | |
| Payment | payments | Đủ | |
| Invoice | invoices | Đủ | |
| «service» ReportService | – | – | Lớp dịch vụ, không lưu dữ liệu |

## 2. Danh sách điểm không khớp / cần chốt

| # | Ở đâu | Vấn đề | Đề xuất | Người sửa | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| 1 | Class – mọi khóa | Class ghi mọi mã là `string` (`orderId: string`…), CSDL dùng `INT AUTO_INCREMENT` | NV3 đổi kiểu mã thành `int` (riêng `sessionId` giữ `string`) | NV3 | Mở |
| 2 | Class – User | Class tên `User`, thuộc tính `accountId`, ghi chú nói bảng `ACCOUNT` → tên không thống nhất | Giữ class `User`, ghi chú rõ "ánh xạ bảng `accounts`"; hoặc đổi class thành `Account` | NV3 | Mở |
| 3 | Class – User.status | Chưa ghi giá trị | Thêm vào ghi chú: `ACTIVE / LOCKED` | NV3 | Mở |
| 4 | Class – MenuItem.status | Chưa ghi giá trị; `deleteMenuItem()` nếu xóa thật sẽ làm lỗi khóa ngoại của `order_items` và mất dữ liệu báo cáo | Thêm giá trị `AVAILABLE / SOLD_OUT / DELETED`; `deleteMenuItem()` chỉ đổi sang `DELETED` (xóa mềm) | NV3 | Mở |
| 5 | Class – KitchenTicket.status | Chưa ghi giá trị | Thêm `SENT / IN_PROGRESS / COMPLETED` | NV3 | Mở |
| 6 | Class – Payment.status, Discount.type | Chưa ghi giá trị | Payment: `PENDING / SUCCESS / FAILED`; Discount: `PERCENT / FIXED` | NV3 | Mở |
| 7 | FR-06, FR-07 và OrderItem | Trạng thái món không phân biệt "chưa gửi bếp" và "đã gửi, bếp chưa nhận" (đều là `PENDING`) | Quy ước: `ticket_id` NULL = chưa gửi bếp. `canModify()` = true khi `PENDING` hoặc `RECEIVED`. NV2 ghi đúng quy tắc này trong mô tả use case sửa/hủy món | NV2, NV3 | Mở |
| 8 | FR-09 và Notification | Thông báo gắn với Waiter, nhưng đơn do khách tự gọi thì không có `created_by_account_id` → không biết gửi cho ai | Chốt: gửi cho nhân viên phụ trách bàn, hoặc gửi cho mọi Waiter đang trực. NV2 ghi vào use case "Nhận thông báo món xong" | NV2, NV3 | Mở |
| 9 | Phạm vi và Customer | Tích điểm nằm ngoài phạm vi, khách không đăng nhập, nhưng class Customer có `fullName`, `phone` → giao diện khách có hỏi tên, số điện thoại không? | NV1 xác nhận màn hình khách tự gọi món có/không hỏi thông tin; nếu không, có thể bỏ class Customer | NV1, NV3 | Mở |
| 10 | FR-10 và Order | FR-10 yêu cầu tính thuế; Order có `taxAmount` nhưng không class nào lưu thuế suất (%) để tính | Chốt một trong hai: thuế suất là hằng số cấu hình của hệ thống (ghi vào mô tả `calculateTotal()`), hoặc thêm thuộc tính `taxRate` vào Order (NV4 thêm cột `orders.tax_rate`) | NV3 | Mở |

## 3. Đối chiếu tên trạng thái giữa yêu cầu và thiết kế

Gửi bảng này cho NV1, NV2 để wireframe và use case dùng đúng tên.

| Yêu cầu (tiếng Việt) | Class / CSDL |
| --- | --- |
| Bàn: trống / đang dùng / đã đặt (FR-03) | `AVAILABLE / OCCUPIED / RESERVED` |
| Món ở bếp: đã nhận / đang làm / xong (FR-08) | `RECEIVED / COOKING / DONE` (thêm `PENDING`, `CANCELLED`) |
| Thanh toán: tiền mặt / thẻ / chuyển khoản (FR-11) | `CASH / CARD / TRANSFER` |
| Đơn hàng | `DRAFT / CONFIRMED / PAID / CANCELLED` |
| Nhân viên phục vụ / Bếp / Thu ngân / Quản lý | `WAITER / CHEF / CASHIER / MANAGER` (class Waiter / Chef / Cashier / Manager, bảng `accounts`) |
| Khách hàng | class Customer, bảng `customers` (không có tài khoản, không thuộc `roles`) |

## 4. Việc còn lại

- [ ] Khi NV1 đẩy DFD: đối chiếu kho dữ liệu DFD mức 1 với bảng ở mục 1.
- [ ] Khi NV2 đẩy Use Case: đối chiếu 5 actor và các use case với FR.
- [ ] Khi NV1, NV2 đẩy wireframe: mỗi ô nhập liệu phải có cột lưu.
- [ ] NV3 sửa các điểm 1–8 và 10, NV4 cập nhật lại ERD nếu có thay đổi.
