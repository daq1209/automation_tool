import concurrent.futures
import streamlit as st
from src.repositories import woo, db
from src.utils.common import get_val

def worker_check_product(row, domain, secret, index):
    """
    Worker này chỉ có nhiệm vụ Kiểm tra và Trả về kết quả (KHÔNG GHI SHEET).
    """
    sku = get_val(row, ['SKU', 'sku', 'ID', 'id', 'Product ID'])
    if not sku:
        return None

    # Lấy trạng thái hiện tại trên Sheet
    # Giả sử cột đầu tiên (index 0) là cột Status/Check_update
    current_sheet_status = str(list(row.values())[0]).strip().lower()

    # Gọi API check
    is_exist = woo.check_product_exists(domain, secret, sku)
    
    if is_exist is True:
        new_status = "Done"
    elif is_exist is False:
        new_status = "Holding"
    else:
        # Nếu lỗi kết nối thì giữ nguyên hoặc báo Error, ở đây ta tạm bỏ qua để không ghi đè bậy
        return None

    # Chỉ cập nhật nếu trạng thái thay đổi
    if current_sheet_status != new_status.lower():
        return {
            'row_index': index,
            'status': new_status,
            'sku': sku,
            'old_status': current_sheet_status
        }
    
    return None

def process_check_existence(data_rows, domain, secret, sheet_id, tab_name, max_workers=10, progress_callback=None):
    logs = []
    batch_data = []
    
    # 1. Quét dữ liệu (Đa luồng) - Bước này chạy rất nhanh
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Tạo dictionary để map future với index dòng
        future_to_row = {
            executor.submit(worker_check_product, row, domain, secret, i + 2): (i + 2)
            for i, row in enumerate(data_rows)
        }
        
        total_items = len(data_rows)
        processed_count = 0
        
        for future in concurrent.futures.as_completed(future_to_row):
            processed_count += 1
            res = future.result()
            
            if res:
                # Nếu có kết quả cần thay đổi, thêm vào danh sách chờ ghi
                batch_data.append({
                    'range': f'A{res["row_index"]}',  # Giả định cột Status là cột A
                    'values': [[res['status']]]
                })
                logs.append(f"Row {res['row_index']}: {res['old_status']} -> {res['status']} ({res['sku']})")
            
            # Cập nhật tiến độ trên UI
            if progress_callback:
                progress_callback(processed_count / total_items, processed_count, total_items)

    # 2. Ghi xuống Sheet (1 Lần duy nhất) - Giải quyết triệt để lỗi 429
    if batch_data:
        logs.append(f"--- Đang ghi {len(batch_data)} thay đổi xuống Sheet... ---")
        db.update_sheet_batch(sheet_id, tab_name, batch_data)
        logs.append("--- Ghi dữ liệu hoàn tất! ---")
    else:
        logs.append("--- Không có dữ liệu nào cần cập nhật ---")
                
    return logs