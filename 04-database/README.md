# 04-database – NV4: Cơ sở dữ liệu và kiểm tra chéo

Thiết kế CSDL 18 bảng (MySQL 8) cho hệ thống quản lý gọi món nhà hàng, ánh xạ từ class diagram của NV3.

## Sản phẩm

| Yêu cầu NV4 | File |
| --- | --- |
| ERD (vẽ bằng draw.io) | [`erd.drawio`](erd.drawio) – trang 1: mô hình thực thể – kết hợp; trang 2: lược đồ quan hệ (bảng, khóa ngoại) |
| Bảng mô tả cấu trúc CSDL | [`database-specification.md`](database-specification.md) |
| Danh sách lỗi không khớp | [`cross-check.md`](cross-check.md) |
| Phụ lục: script tạo bảng | [`appendix/schema.sql`](appendix/schema.sql) |
| Phụ lục: truy vấn báo cáo FR-12 | [`appendix/report-queries.sql`](appendix/report-queries.sql) |

## Cách xem / chạy

- **Xem / sửa ERD:** mở [app.diagrams.net](https://app.diagrams.net) → File → Open from → Device → chọn `erd.drawio`.
- **Xuất ảnh cho báo cáo:** trong draw.io chọn File → Export as → PNG.
- **Tạo CSDL:** mở MySQL Workbench (hoặc phpMyAdmin), chạy `appendix/schema.sql`. Script tự tạo database `restaurant_order_management` với `utf8mb4` để lưu tiếng Việt.
