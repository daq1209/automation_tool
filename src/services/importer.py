import concurrent.futures
from src.repositories import woo, db
from src.utils.common import get_val

# --- WORKER IMPORT DATA (GIỮ NGUYÊN) ---
def worker_import_data(row, api_domain, secret, index, sheet_id, tab_name):
    sheet_id_val = get_val(row, ['ID', 'id', 'Product ID'])
    sheet_sku_val = get_val(row, ['SKU', 'sku', 'Model'])
    final_sku = sheet_id_val if sheet_id_val else sheet_sku_val
    
    if not final_sku:
        return False, f"Row {index}: Skipped (Missing ID/SKU)", {'row': index, 'status': 'Error: Missing ID'}

    title = get_val(row, ['Name', 'Title', 'title'])
    price = get_val(row, ['Regular price', 'Price', 'price'])
    description = get_val(row, ['Description', 'description'])
    
    payload = { "sku": final_sku, "title": title, "price": price, "description": description }
    
    res = woo.post_product_data(api_domain, secret, payload)
    
    if res and res.status_code == 200:
        return True, f"Row {index}: Data OK (SKU: {final_sku})", {'row': index, 'status': 'Done'}
    elif res:
        return False, f"Row {index}: Failed - {res.status_code}", {'row': index, 'status': f'Error {res.status_code}'}
    else:
        return False, f"Row {index}: Connection Error", {'row': index, 'status': 'Connection Error'}

# --- WORKER IMPORT IMAGE (GIỮ NGUYÊN) ---
def worker_import_image(row, api_domain, secret, index, sheet_id, tab_name):
    sheet_id_val = get_val(row, ['ID', 'id', 'Product ID'])
    sheet_sku_val = get_val(row, ['SKU', 'sku'])
    final_sku = sheet_id_val if sheet_id_val else sheet_sku_val

    raw_images = get_val(row, ['Images', 'images', 'Image URL', 'Image Src'])
    image_list = []
    if raw_images:
        clean_str = raw_images.replace('\n', ',').replace('\r', '')
        parts = clean_str.split(',')
        for p in parts:
            clean_url = p.strip().strip('"').strip("'")
            if clean_url: image_list.append(clean_url)

    if not image_list: return False, None, None
    if not final_sku: return False, f"Row {index}: Missing ID", {'row': index, 'status': 'Missing ID'}

    payload = { "sku": final_sku, "images": image_list }
    res = woo.post_product_image(api_domain, secret, payload)
    
    if res and res.status_code == 200:
        return True, f"Row {index}: Img Success", {'row': index, 'status': 'Done'}
    elif res and res.status_code == 404:
        return False, f"Row {index}: SKU Not Found", {'row': index, 'status': 'Error 404'}
    elif res:
        return False, f"Row {index}: Error {res.status_code}", {'row': index, 'status': f'Error {res.status_code}'}
    else:
        return False, f"Row {index}: Timeout", {'row': index, 'status': 'Timeout'}

# --- MANAGER FUNCTION (CẬP NHẬT LOGIC ROW INDEX) ---
def process_import(data_rows, domain, secret, mode, sheet_id, tab_name, max_workers=4, progress_callback=None):
    logs = []
    batch_updates = []
    
    total_items = len(data_rows)
    count_ok = 0
    count_fail = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, row in enumerate(data_rows):
            # [FIX]: Lấy số dòng gốc từ biến '_real_row' nếu có (do UI truyền vào)
            # Nếu không có (chạy all rows) thì mới dùng i + 2
            real_row_idx = row.get('_real_row', i + 2)
            
            if mode == 'data':
                futures.append(executor.submit(worker_import_data, row, domain, secret, real_row_idx, sheet_id, tab_name))
            else:
                futures.append(executor.submit(worker_import_image, row, domain, secret, real_row_idx, sheet_id, tab_name))
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if progress_callback:
                progress_callback((i + 1) / total_items, i + 1, total_items)
            
            is_ok, msg, update_info = future.result()
            
            if msg:
                if is_ok: count_ok += 1
                else: 
                    count_fail += 1
                    logs.append(msg)
            
            if update_info:
                # Update vào đúng dòng gốc trong sheet
                batch_updates.append({
                    'range': f'A{update_info["row"]}',
                    'values': [[update_info['status']]]
                })

    if batch_updates:
        logs.append(f"--- Syncing {len(batch_updates)} rows to Google Sheet... ---")
        db.update_sheet_batch(sheet_id, tab_name, batch_updates)
        logs.append("--- Sync Completed! ---")
                    
    logs.append(f"SUMMARY: Success {count_ok} | Failed {count_fail}")
    return logs