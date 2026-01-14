import concurrent.futures
from src.repositories import woo, db

# --- WORKERS ---
def worker_delete_media(ids_chunk, domain, secret):
    success = woo.delete_media_batch(domain, secret, ids_chunk)
    return success, len(ids_chunk)

def worker_delete_product(ids_chunk, domain, ck, cs):
    # Hàm này xóa batch, không hỗ trợ ghi sheet từng dòng chi tiết trong batch
    # Để ghi sheet chính xác, ta nên xóa từng ID hoặc update sheet theo batch.
    success, count = woo.delete_products_batch(domain, ck, cs, ids_chunk)
    return success, count

def worker_delete_single_product_with_sync(id, domain, ck, cs, index, sheet_id, tab_name):
    """Worker xóa 1 sản phẩm và ghi sheet (Chậm hơn batch nhưng đồng bộ chính xác)"""
    # Vì API Batch trả về kết quả gộp, nên nếu muốn update từng dòng sheet chính xác
    # ta nên gọi xóa từng cái HOẶC update sheet cả cụm.
    # Ở đây chọn giải pháp: Xóa batch -> Update sheet cả cụm.
    pass 

# --- MAIN FUNCTIONS ---

def delete_all_media(domain, secret, max_workers=10, progress_callback=None):
    all_ids = woo.get_all_media_ids(domain, secret)
    total = len(all_ids)
    
    if total == 0: return True, "Media library is already empty."
    
    chunk_size = 50
    chunks = [all_ids[i:i + chunk_size] for i in range(0, total, chunk_size)]
    deleted_total = 0
    total_chunks = len(chunks)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_delete_media, chunk, domain, secret) for chunk in chunks]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            is_ok, count = future.result()
            if is_ok: deleted_total += count
            if progress_callback:
                progress_callback((i + 1) / total_chunks, deleted_total, total)
                
    return True, f"Cleaned up {deleted_total}/{total} images."

# --- HÀM XÓA DANH SÁCH (Mode Text Area - Không cần Sync Sheet) ---
def delete_product_list(domain, ck, cs, id_list, max_workers=5, progress_callback=None):
    if not id_list: return ["List empty"]
    chunk_size = 100
    chunks = [id_list[i:i + chunk_size] for i in range(0, len(id_list), chunk_size)]
    deleted_total = 0
    total_chunks = len(chunks)
    total_items = len(id_list)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_delete_product, chunk, domain, ck, cs) for chunk in chunks]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            is_ok, count = future.result()
            if is_ok: deleted_total += count
            if progress_callback:
                progress_callback((i + 1) / total_chunks, deleted_total, total_items)
                
    return [f"Successfully deleted {deleted_total}/{total_items} items."]

# --- HÀM XÓA TỪ SHEET (Mode Sync - Có ghi 'Done') ---
def process_delete_from_sheet(data_rows, domain, ck, cs, sheet_id, tab_name, max_workers=5, progress_callback=None):
    """Hàm này dùng cho chức năng xóa từ file Delete.csv"""
    logs = []
    
    # 1. Lọc ra các ID chưa Done
    pending_items = [] # List chứa (ID, RowIndex)
    
    for i, row in enumerate(data_rows):
        real_row_idx = i + 2
        # Cột 1 là trạng thái, Cột 2 là ID (theo file Delete.csv mẫu)
        vals = list(row.values())
        status = str(vals[0]).strip().lower()
        pid = str(vals[1]).strip()
        
        if status != 'done' and pid:
            pending_items.append({'id': pid, 'row': real_row_idx})

    total_pending = len(pending_items)
    if total_pending == 0:
        return ["All items are already deleted (Done)."]

    # 2. Xóa theo Batch (để nhanh) nhưng Update Sheet theo Batch
    chunk_size = 50
    # Chia pending_items thành các gói nhỏ
    batches = [pending_items[i:i + chunk_size] for i in range(0, total_pending, chunk_size)]
    
    deleted_count = 0
    
    def worker_batch_sync(batch_items):
        # Lấy list ID trong batch này
        ids_to_del = [item['id'] for item in batch_items]
        # Gọi API xóa
        success, count = woo.delete_products_batch(domain, ck, cs, ids_to_del)
        
        if success:
            # Nếu xóa thành công cả gói -> Update sheet cho từng dòng trong gói
            for item in batch_items:
                db.update_row_status(sheet_id, tab_name, item['row'], "Done")
            return True, count
        else:
            # Nếu lỗi cả gói
            for item in batch_items:
                db.update_row_status(sheet_id, tab_name, item['row'], "Error")
            return False, 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_batch_sync, batch) for batch in batches]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            is_ok, count = future.result()
            if is_ok: deleted_count += count
            
            if progress_callback:
                progress_callback((i + 1) / len(batches), deleted_count, total_pending)

    return [f"Deleted {deleted_count}/{total_pending} items from Sheet."]

def delete_all_products_scan_mode(domain, ck, cs, max_workers=10, progress_callback=None):
    res1 = woo.fetch_product_ids_page(domain, ck, cs, 1)
    if not res1 or res1.status_code != 200: return ["Connection Failed"]
    
    total_pages = int(res1.headers.get('X-WP-TotalPages', 0))
    all_ids = [p['id'] for p in res1.json()]
    
    if total_pages > 1:
        pages = list(range(2, total_pages + 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_fetch_page, p, domain, ck, cs) for p in pages]
            for future in concurrent.futures.as_completed(futures):
                all_ids.extend(future.result())
    
    if not all_ids: return ["Store is already clean."]
    return delete_product_list(domain, ck, cs, all_ids, max_workers, progress_callback)