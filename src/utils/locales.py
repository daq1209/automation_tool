"""
Localization dictionary for POD Automation Environment.
Supports English (en) and Vietnamese (vi).
"""

TRANS = {
    # --- SIDEBAR & COMMON ---
    "nav_title": {
        "en": "Admin Console",
        "vi": "Bảng Điều Khiển"
    },
    "nav_menu_label": {
        "en": "Menu",
        "vi": "Danh mục"
    },
    "nav_dashboard": {
        "en": "Dashboard",
        "vi": "Tổng quan"
    },
    "nav_updater": {
        "en": "Data Updater",
        "vi": "Cập nhật Dữ liệu"
    },
    "nav_user_mgmt": {
        "en": "User Management",
        "vi": "Quản lý Người dùng"
    },
    "logout_btn": {
        "en": "Logout",
        "vi": "Đăng xuất"
    },
    "env_label": {
        "en": "Environment: Production",
        "vi": "Môi trường: Production"
    },
    "settings_label": {
        "en": "Advanced Settings",
        "vi": "Cài đặt Nâng cao"
    },
    "threads_label": {
        "en": "Worker Threads:",
        "vi": "Luồng xử lý (Threads):"
    },
    
    # --- SITE SELECTION ---
    "site_select_header": {
        "en": "1. Target Website",
        "vi": "1. Chọn Website"
    },
    "site_select_label": {
        "en": "Select Website to Start:",
        "vi": "Chọn Website để bắt đầu:"
    },
    "site_select_default": {
        "en": "-- Select a Website --",
        "vi": "-- Chọn Website --"
    },
    "site_select_prompt": {
        "en": "Please select a website to proceed.",
        "vi": "Vui lòng chọn một website để tiếp tục."
    },
    
    # --- TABS ---
    "tab_import": {
        "en": "Import Pipeline (V12)",
        "vi": "Quy trình Import"
    },
    "tab_delete": {
        "en": "Delete Tool",
        "vi": "Công cụ Xóa"
    },
    "tab_images": {
        "en": "Images",
        "vi": "Hình ảnh"
    },
    
    # --- IMPORT TAB ---
    "guide_import_title": {
        "en": "User Guide: Import Pipeline",
        "vi": "Hướng dẫn: Quy trình Import"
    },
    "guide_import_content": {
        "en": """
        **How to use:**
        1. **Configuration**: Select the Sheet Tabs for Data and Images.
        2. **Import Scope**:
           - *Import All Rows*: Processes every row in the Google Sheet.
           - *Filter by IDs*: Processes only specific Product IDs/SKUs (comma or newline separated).
        3. **Preview**: Check 'Preview Data' to see what will be imported.
        4. **Run**: Click 'RUN IMPORT PROCESS' to start.
        """,
        "vi": """
        **Cách sử dụng:**
        1. **Cấu hình**: Chọn Tab Sheet chứa Dữ liệu và Hình ảnh.
        2. **Phạm vi Import**:
           - *Import All Rows*: Xử lý tất cả các dòng trong Sheet.
           - *Filter by IDs*: Chỉ xử lý các ID/SKU cụ thể (cách nhau bởi dấu phẩy hoặc xuống dòng).
        3. **Xem trước**: Tích chọn 'Xem trước Dữ liệu' để kiểm tra.
        4. **Chạy**: Nhấn 'CHẠY QUY TRÌNH IMPORT' để bắt đầu.
        """
    },
    "config_header": {
        "en": "Configuration",
        "vi": "Cấu hình"
    },
    "tab_data_label": {
        "en": "Data Tab Name:",
        "vi": "Tên Tab Dữ liệu:"
    },
    "tab_img_label": {
        "en": "Image Tab Name:",
        "vi": "Tên Tab Hình ảnh:"
    },
    "import_scope_header": {
        "en": "Import Scope",
        "vi": "Phạm vi Import"
    },
    "mode_label": {
        "en": "Mode:",
        "vi": "Chế độ:"
    },
    "mode_all": {
        "en": "Import All Rows",
        "vi": "Import Tất cả"
    },
    "mode_filter": {
        "en": "Filter by Specific IDs",
        "vi": "Lọc theo ID cụ thể"
    },
    "filter_input_label": {
        "en": "Sheet IDs:",
        "vi": "Nhập Sheet IDs:"
    },
    "preview_chk": {
        "en": "Preview Data (Applied Filter)",
        "vi": "Xem trước Dữ liệu (Đã lọc)"
    },
    "refresh_btn": {
        "en": "Refresh Data",
        "vi": "Làm mới Dữ liệu"
    },
    "run_import_btn": {
        "en": "RUN IMPORT PROCESS",
        "vi": "CHẠY QUY TRÌNH IMPORT"
    },
    "import_note": {
        "en": "Note: Successful imports -> 'Done' | Published -> '1'",
        "vi": "Ghi chú: Import thành công -> 'Done' | Đã đăng -> '1'"
    },

    # --- DELETE TAB ---
    "guide_delete_title": {
        "en": "User Guide: Delete Products",
        "vi": "Hướng dẫn: Xóa Sản phẩm"
    },
    "guide_delete_content": {
        "en": """
        **Modes:**
        - **Visual Selection**: Search for products by ID/SKU, select them, and delete. Safe mode.
        - **Wipe All**: **DANGER!** Deletes ALL products on the website. Use with extreme caution.
        """,
        "vi": """
        **Chế độ:**
        - **Chọn thủ công**: Tìm kiếm sản phẩm theo ID/SKU, chọn và xóa. Chế độ an toàn.
        - **Xóa sạch (Wipe All)**: **NGUY HIỂM!** Xóa TOÀN BỘ sản phẩm trên website. Cẩn trọng khi dùng.
        """
    },
    "tab_del_prod": {
        "en": "Delete Products",
        "vi": "Xóa Sản phẩm"
    },
    "tab_del_media": {
        "en": "Delete Media",
        "vi": "Xóa Media"
    },
    "mode_visual": {
        "en": "Visual Selection",
        "vi": "Chọn thủ công"
    },
    "mode_wipe": {
        "en": "Wipe All",
        "vi": "Xóa sạch (Wipe All)"
    },
    "search_label": {
        "en": "Search ID/SKU:",
        "vi": "Tìm ID/SKU:"
    },
    "fetch_btn": {
        "en": "Fetch",
        "vi": "Tìm kiếm"
    },
    "delete_sel_btn": {
        "en": "Delete {} items",
        "vi": "Xóa {} mục"
    },
    "danger_warn": {
        "en": "DANGER: This will delete ALL products on the website.",
        "vi": "CẢNH BÁO: Hành động này sẽ xóa TOÀN BỘ sản phẩm trên website."
    },
    "confirm_wipe_btn": {
        "en": "CONFIRM WIPE ALL PRODUCTS",
        "vi": "XÁC NHẬN XÓA TOÀN BỘ"
    },

    # --- IMAGE TAB ---
    "guide_img_title": {
        "en": "User Guide: Image Sync",
        "vi": "Hướng dẫn: Đồng bộ Ảnh"
    },
    "guide_img_content": {
        "en": """
        **Purpose**: Synchronize Media Library from WordPress back to Google Sheets.
        **Logic**: Matches WP media to Sheet items by ID or Slug.
        """,
        "vi": """
        **Mục đích**: Đồng bộ Thư viện Media từ WordPress ngược về Google Sheets.
        **Logic**: Khớp media từ WP với dòng trong Sheet qua ID hoặc Slug.
        """
    },
    "sync_header": {
        "en": "Sync WordPress Media to Sheet",
        "vi": "Đồng bộ Media từ WP về Sheet"
    },
    "limit_label": {
        "en": "Max Media to Fetch:",
        "vi": "Giới hạn số lượng:"
    },
    "preview_sheet_chk": {
        "en": "Preview Sheet Data",
        "vi": "Xem trước Sheet"
    },
    "run_sync_btn": {
        "en": "RUN MEDIA SYNC",
        "vi": "CHẠY ĐỒNG BỘ MEDIA"
    },

    # --- UPDATER ---
    "updater_title": {
        "en": "CSV Data Updater",
        "vi": "Cập nhật Dữ liệu CSV"
    },
    "guide_updater_title": {
        "en": "User Guide: CSV Data Updater",
        "vi": "Hướng dẫn: Cập nhật CSV"
    },
    "guide_updater_content": {
        "en": """
        **Workflow:**
        1. **Upload CSV**: Upload file.
        2. **Select Columns**: Choose columns to update.
        3. **Review**: Use 'Select All' and check highlights.
        4. **Run**: Click 'Update'.
        """,
        "vi": """
        **Quy trình:**
        1. **Tải lên CSV**: Chọn file dữ liệu mới.
        2. **Chọn Cột**: Chọn các cột cần cập nhật.
        3. **Kiểm tra**: Dùng 'Chọn Tất cả' và xem các ô được tô màu.
        4. **Chạy**: Nhấn 'Cập nhật'.
        """
    },
    "target_tab_label": {
        "en": "Target Sheet Tab Name:",
        "vi": "Tên Tab Sheet Đích:"
    },
    "upload_label": {
        "en": "Upload CSV Update File",
        "vi": "Tải lên file CSV"
    },
    "review_header": {
        "en": "1. Review & Select Data",
        "vi": "1. Kiểm tra & Chọn Dữ liệu"
    },
    "step1_caption": {
        "en": "Step 1: Choose Columns to Update",
        "vi": "Bước 1: Chọn Cột cần Cập nhật"
    },
    "col_select_label": {
        "en": "Select Columns to Update:",
        "vi": "Chọn Cột:"
    },
    "step2_caption": {
        "en": "Step 2: Check Rows to Process (See Highlighted Preview below)",
        "vi": "Bước 2: Chọn Dòng để Xử lý (Xem phần Tô màu bên dưới)"
    },
    "btn_select_all": {
        "en": "Select All Rows",
        "vi": "Chọn Tất cả"
    },
    "btn_deselect_all": {
        "en": "Deselect All",
        "vi": "Bỏ chọn Tất cả"
    },
    "data_header": {
        "en": "Data from CSV File",
        "vi": "Dữ liệu từ File CSV"
    },
    "highlight_header": {
        "en": "Highlighted Preview (Values to be Updated)",
        "vi": "Xem trước Thay đổi (Các giá trị được tô màu)"
    },
    "highlight_caption": {
        "en": "Values to be updated are highlighted below:",
        "vi": "Các giá trị sẽ được cập nhật được tô màu vàng dưới đây:"
    },
    "processing_stats": {
        "en": "Processing: **{} rows** across **{} columns**.",
        "vi": "Đang xử lý: **{} dòng** trên **{} cột**."
    },
    "update_btn": {
        "en": "Update to Google Sheet",
        "vi": "Cập nhật vào Google Sheet"
    }
}

def get_text(key: str, lang: str = 'en') -> str:
    """Retrieve translated text for a given key and language."""
    item = TRANS.get(key, {})
    return item.get(lang, item.get('en', key))
