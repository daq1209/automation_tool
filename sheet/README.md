#  QUAN TRỌNG - ĐỌC KỸ

## Về Các File CSV Trong Thư Mục Này

Các file CSV trong thư mục `sheet/` này **CHỈ LÀ BẢN COPY** để Antigravity AI có thể tham khảo cấu trúc dữ liệu.

### ❌ KHÔNG được sử dụng các file này để:
- Thực hiện tương tác dữ liệu
- Import/Export trực tiếp
- Cập nhật thông tin sản phẩm

### ✅ Dữ liệu THỰC TẾ được lưu và xử lý tại:

**Google Sheets URL:**
```
https://docs.google.com/spreadsheets/d/1n1IPrJ9iPJyj74RDS7tPN8Jo8_iI2jVawbx8GKpHe78/edit?gid=994278374#gid=994278374
```

**Mục đích của folder này:**
- 📋 Tham khảo cấu trúc dữ liệu
- 🔍 Phân tích headers/columns
- 📊 Backup offline (không đồng bộ real-time)

---

**Lưu ý cho Developers:**
Khi làm việc với hệ thống, luôn truy cập **Google Sheets trực tiếp** thông qua:
- `src/repositories/db.py` → `init_google_sheets()`
- Streamlit UI → Tab "Import Pipeline" hoặc "Delete Tool"

**KHÔNG** edit trực tiếp các file CSV này và expect chúng sẽ sync lên hệ thống.

---

*Cập nhật: 2026-01-21*
