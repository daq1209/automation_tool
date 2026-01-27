# POD Automation Environment

> **Environment:** POD Automation Environment
> **Last Updated:** 2026-01-27

An internal automation system for synchronizing product data between Google Sheets and WordPress/WooCommerce via custom APIs. Now successfully deployed on **Streamlit Cloud**.

---

## 🇻🇳 TIẾNG VIỆT (VIETNAMESE)

### Giới thiệu
Hệ thống tự động hóa nội bộ dùng để đồng bộ dữ liệu sản phẩm giữa Google Sheets và WordPress/WooCommerce thông qua API tùy chỉnh.

### Tài liệu
- **[Tổng quan Hệ thống](docs/SYSTEM_OVERVIEW.md)** - Kiến trúc & chi tiết kỹ thuật
- **[Đánh giá Hệ thống](docs/SYSTEM_ASSESSMENT.md)** - Điểm yếu & kế hoạch cải thiện
- **[Hướng dẫn Di dời](docs/MIGRATION_GUIDE.md)** - Cách nâng cấp lên bản mới nhất

### Tính năng Chính

#### Import Pipeline
- **Xử lý 2 pha:** Dữ liệu văn bản trước, hình ảnh sau.
- **Đa luồng:** Hơn 20 workers chạy đồng thời.
- **Tự động đồng bộ:** Cập nhật trạng thái trực tiếp vào Google Sheet.

#### Smart Image Sync (Mới ở V13)
- **Logic Trạng thái:**
  - `Done`: Cả Tiêu đề VÀ Đường dẫn (Slug) đều khớp với giá trị mới.
  - `Holding`: Đường dẫn vẫn giống giá trị cũ (chờ cập nhật).
  - `Error`: Không khớp hoặc cập nhật lỗi.
- **Kiểm tra 2 chiều:** Xác thực chặt chẽ cả Title & Slug.

#### Công cụ Xóa (Delete Tool)
- **Xóa hàng loạt:** Sản phẩm & Media.
- **Xác thực 2 bước:** Tránh xóa nhầm.

#### Bảo mật
- **Dynamic Keys:** Không lưu cứng trong code.
- **Bcrypt:** Mã hóa mật khẩu an toàn.

### Cấu hình & Sử dụng
1.  **Cài đặt:** `pip install -r requirements.txt`
2.  **Cấu hình:** Chỉnh sửa `.streamlit/secrets.toml` (Supabase & Google Credentials).
3.  **Chạy App:** `streamlit run app.py`

---

## 🇬🇧 ENGLISH

### Overview
Internal automation system for synchronizing product data between Google Sheets and WordPress/WooCommerce via custom APIs.

### Documentation
- **[System Overview](docs/SYSTEM_OVERVIEW.md)**
- **[System Assessment](docs/SYSTEM_ASSESSMENT.md)**
- **[Migration Guide](docs/MIGRATION_GUIDE.md)**

### Key Features

#### Import Pipeline
- **Two-phase processing:** Text data first, images later.
- **Multi-threading:** 20+ concurrent workers.
- **Auto-sync:** Updates Google Sheet statuses.

#### Smart Image Sync (New in V13)
- **Status Logic:**
  - `Done`: Both Title AND Slug match the new values.
  - `Holding`: Slug still matches the old value (pending update).
  - `Error`: Mismatch or update failure.
- **Bi-directional Check:** strict validation of Title & Slug.

#### Delete Tool
- **Batch deletion:** Products & media.
- **Two-factor confirmation:** Prevent accidental deletion.

#### Security
- **Dynamic secret keys:** No hard-coded credentials.
- **Bcrypt hashing:** Secure password storage.

### Configuration & Usage
1.  **Install:** `pip install -r requirements.txt`
2.  **Config:** Edit `.streamlit/secrets.toml`.
3.  **Run:** `streamlit run app.py`

---

## Version History / Lịch sử Phiên bản

### 2026-01-22 - V13.0 Cloud Deployment
- **Deployed to Streamlit Cloud:** Migrated from Google Colab for 24/7 stability.
- **Enhanced UpdateImage Logic:** Added strict `Done`/`Holding`/`Error` status based on Title & Slug verification.
- **UI Improvements:** Added 'Refresh Data' buttons and increased Media Fetch Limit to 200,000 items.
- **Smart Note Sync:** Automatically updates 'API Note' column to 'RENAMED' when slug changes are detected.
- **Fixed Column Mapping:** Improved sheet column detection (case-insensitive, space-friendly).

### 2026-01-21 - V12.5 Quick Wins
- Implemented bcrypt password hashing.
- Added structured logging system.

---

## Support / Hỗ trợ
- **Logs:** Check `logs/app.log`
- **Maintainer:** Admin Team

---

## License
Internal use only.
