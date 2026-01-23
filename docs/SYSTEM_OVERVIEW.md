# POD Automation System - Tổng Quan Hệ Thống

> **Phiên bản:** V12.5 Enterprise  
> **Công nghệ:** Python (Streamlit) + WordPress (Custom API)  
> **Mục đích:** Tự động hóa quản lý và đồng bộ dữ liệu sản phẩm giữa Google Sheets và WooCommerce

---

## 📋 Mô Tả Chức Năng

Hệ thống này là một **ETL Automation Tool** với khả năng **Two-Way Sync**, cho phép:

1. **Import hàng loạt** sản phẩm từ Google Sheets lên WordPress/WooCommerce
2. **Xóa hàng loạt** sản phẩm/media trên WooCommerce và cập nhật trạng thái ngược lại Sheet
3. **Đồng bộ hai chiều** để duy trì tính nhất quán giữa Sheet và Website
4. **Quản lý phân tán** nhiều website từ một giao diện tập trung

---

## 🏗️ Kiến Trúc Hệ Thống

### 1. **Frontend (Streamlit App)**

#### Entry Point
```
app.py
├── Login UI (login_ui.py)
└── Main Dashboard (main_ui.py)
    ├── Import Pipeline
    ├── Delete Tool
    └── Auto Sync
```

#### Các Module Chính

**`src/ui/`** - Giao diện người dùng
- `login_ui.py`: Xác thực admin qua Supabase
- `main_ui.py`: Dashboard chính với 2 tab:
  - **Import Pipeline**: Upload sản phẩm với filter và preview
  - **Delete Tool**: Xóa sản phẩm/media (visual selection hoặc wipe all)

**`src/services/`** - Business Logic Layer
- `importer.py`: Xử lý import 2 pha (Data → Images background)
- `deleter.py`: Xóa sản phẩm/media và sync trạng thái về Sheet
- `checker.py`: Sync hai chiều giữa Sheet và WP

**`src/repositories/`** - Data Access Layer
- `db.py`: Kết nối Supabase (admin users, woo_sites) + Google Sheets API
- `woo.py`: Custom API endpoints cho WooCommerce

**`src/utils/`** - Tiện ích
- `common.py`: Helpers (CSS loader, column mapping, UI lock screen)

---

### 2. **Backend (WordPress Custom API)**

#### Namespace: `/wp-json/test-secret/v1/`

**Bảo mật:** Dynamic Secret Key (lưu trong `wp_options` table)

#### Các Endpoint Chính

| Endpoint | Method | Chức năng |
|----------|--------|-----------|
| `/get-all-skus` | GET | Lấy toàn bộ SKU (siêu tốc bằng raw SQL) |
| `/import-product-batch` | POST | Import batch sản phẩm + queue ảnh |
| `/process-pending-media` | POST | Worker xử lý ảnh background (dedup) |
| `/delete-product-batch` | POST | Xóa batch sản phẩm |
| `/delete-media-batch` | POST | Xóa batch media |
| `/check-product` | POST | Kiểm tra sản phẩm tồn tại |
| `/get-product-list` | GET | Lấy danh sách sản phẩm (với search) |
| `/get-media-list` | GET | Lấy danh sách media (với search) |

#### Tính Năng Đặc Biệt
- **Image Deduplication**: Dùng `md5(url)` hash để tránh tải ảnh trùng
- **Atomic Lock**: Dùng `UPDATE ... WHERE` để tránh race condition khi worker đồng thời xử lý
- **Batch Processing**: Xử lý tối đa 50 items/lần để tránh timeout

---

### 3. **Data Layer**

#### Google Sheets Structure

| Cột | Mapping Keys | Mục đích |
|-----|--------------|----------|
| `Check_update` (A) | Status | `Done`, `Holding`, `Error` |
| `ID` | `id`, `Product ID` | SKU chính |
| `Name` | `title` | Tên sản phẩm |
| `Regular price` | `price` | Giá sản phẩm |
| `Description` | `description` | Mô tả |
| `Images` | `images`, `Image URL` | URL (ngăn cách bởi `,` hoặc `\n`) |
| `Published` | `is_published` | `1` (Done) / `-1` (Holding) |

#### Supabase Tables

**`admin_users`**
- `username`, `password`: Xác thực đăng nhập

**`woo_sites`**
- `site_name`: Tên hiển thị
- `domain_url`: URL website
- `secret_key`: API key bảo mật
- `google_sheet_id`: ID của Google Sheet tương ứng
- `consumer_key`, `consumer_secret`: (Legacy WooCommerce API)

---

## 🔄 Quy Trình Hoạt Động

### **Import Flow (2-Phase)**

```
┌─────────────────┐
│ Google Sheet    │
│ (Filter by IDs) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Phase 1: Data Upload (Fast)    │
│ - POST /import-product-batch    │
│ - Queue images (không tải ngay) │
│ - Update Sheet: Done | 1        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Phase 2: Background Images      │
│ - Chạy 20 workers song song     │
│ - POST /process-pending-media   │
│ - Image deduplication (md5)     │
│ - Chỉ tạo thumbnail (tối ưu)    │
└─────────────────────────────────┘
```

### **Delete Flow + Sync**

```
┌──────────────────┐
│ Delete Products  │
│ (Visual/Wipe All)│
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────┐
│ POST /delete-product-batch      │
│ - Trả về deleted SKUs           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│ Sync Back to Sheet              │
│ - Status → Holding              │
│ - Published → -1                │
└─────────────────────────────────┘
```

### **Two-Way Sync**

```
┌──────────────────┐
│ GET /get-all-skus│ (SQL siêu tốc)
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────┐
│ So sánh với Sheet                 │
│ - Có trên WP → Done | 1           │
│ - Không trên WP → Holding | -1    │
└──────────────────────────────────┘
```

---

## 🔐 Bảo Mật

### **Authentication Flow**

1. **Frontend**: Login qua Supabase (`admin_users` table)
2. **API**: Mỗi request gửi `x-secret` header
3. **Backend**: So sánh với `get_option('pod_automation_secret_key')` dùng `hash_equals()` (chống timing attack)

### **Key Management**

- **WP Admin Panel**: Settings → POD Automation Key
- Có nút "Regenerate Key" khi nghi ngờ bị lộ
- Key tự động sinh lần đầu cài đặt

---

## ⚙️ Cấu Hình

### **Secrets (.streamlit/secrets.toml)**

```toml
[supabase]
url = "https://xxx.supabase.co"
key = "sb_publishable_xxx"

[google]
service_account_base64 = "ewogIC..."  # Base64 encodded JSON
```

### **Environment Variables**

- `SUPA_URL`: Supabase URL
- `SUPA_KEY`: Supabase Anon Key

---

## 📊 Trạng Thái Sản Phẩm

| Trạng thái | Cột A (Status) | Cột Published | Ý nghĩa |
|------------|----------------|---------------|---------|
| **Chưa xử lý** | (trống) | 0 hoặc -1 | Chưa import |
| **Import thành công** | `Done` | `1` | Đã lên WP |
| **Đã xóa khỏi WP** | `Holding` | `-1` | Trên Sheet nhưng không trên WP |
| **Lỗi** | `Error: ...` | (giữ nguyên) | Import thất bại |

---

## 🚀 Cách Chạy

### **1. Cài Đặt**

```bash
cd "c:\Tài liệu học\test"
python -m venv venv
.\venv\Scripts\activate
pip install streamlit gspread supabase pandas requests google-auth
```

### **2. Cấu Hình**

- Copy `service_account.json` → Encode bằng `encode_json.py` → Paste vào `secrets.toml`
- Cập nhật Supabase URL/Key trong `secrets.toml`
- Lấy Secret Key từ WP Admin → Cập nhật vào Supabase table `woo_sites`

### **3. Chạy**

```bash
streamlit run app.py
```

Mở trình duyệt: `http://localhost:8501`

---

## 🛠️ Tối Ưu Đã Thực Hiện

1. **Import 2 pha** → Tách Text upload (nhanh) và Image download (background)
2. **SQL thuần** cho `/get-all-skus` → Nhanh hơn 10x so với WooCommerce REST API
3. **Image dedup** → Tránh tải lại ảnh trùng
4. **Batch processing** → 50 items/lần
5. **Multi-threading** → 20 workers cho Phase 2
6. **Atomic lock** → `UPDATE ... WHERE meta_value='yes'` tránh race condition
7. **Chỉ tạo thumbnail** → Không tạo size medium/large thừa

---

## 📁 Cấu Trúc Thư Mục

```
test/
├── app.py                    # Entry point
├── style.css                 # Custom CSS
├── .streamlit/
│   └── secrets.toml         # Sensitive credentials
├── src/
│   ├── ui/
│   │   ├── login_ui.py
│   │   └── main_ui.py
│   ├── services/
│   │   ├── importer.py
│   │   ├── deleter.py
│   │   └── checker.py
│   ├── repositories/
│   │   ├── db.py
│   │   └── woo.py
│   └── utils/
│       └── common.py
├── sheet/                   # Local CSV backups
└── docs/                    # Documentation
```

---

## 🔮 Tính Năng Dự Kiến (tasks.txt)


- [x] Chuyển đổi hardcode key thành dynamic key
- [x] Tích hợp hiển thị trực tiếp dữ liệu Sheet
- [x] Tối ưu tốc độ tải dữ liệu
- [x] Two-way sync với log tracking

---

## 📞 Liên Hệ & Support

- **Database**: Supabase (Postgres)
- **Sheet API**: Google Sheets API v4
- **Framework**: Streamlit 1.x
- **WP**: WordPress 6.x + WooCommerce

---

*Tài liệu được tạo tự động bởi Antigravity AI - 2026-01-21*
