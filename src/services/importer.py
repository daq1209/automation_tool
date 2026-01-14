import concurrent.futures
from src.repositories import woo, db
from src.utils.common import get_val

# --- WORKER FUNCTIONS ---
def worker_import_data(row, api_domain, secret, index, sheet_id, tab_name):
    sku = get_val(row, ['SKU', 'sku', 'ID', 'id'])
    
    if not sku: 
        msg = "Error: Missing SKU"
        db.update_row_status(sheet_id, tab_name, index, msg)
        return False, f"Row {index}: Skipped ({msg})"

    title = get_val(row, ['Name', 'Title', 'title'])
    price = get_val(row, ['Regular price', 'Price', 'price'])
    description = get_val(row, ['Description', 'description'])
    
    payload = { "sku": sku, "title": title, "price": price, "description": description }
    
    res = woo.post_product_data(api_domain, secret, payload)
    
    if res and res.status_code == 200:
        db.update_row_status(sheet_id, tab_name, index, "Done")
        return True, f"Row {index}: Data OK ({sku})"
    elif res:
        err_msg = f"Error {res.status_code}"
        db.update_row_status(sheet_id, tab_name, index, err_msg)
        return False, f"Row {index}: Failed ({sku}) - {err_msg}"
    else:
        db.update_row_status(sheet_id, tab_name, index, "Connection Error")
        return False, f"Row {index}: Connection Error"

def worker_import_image(row, api_domain, secret, index, sheet_id, tab_name):
    sku = get_val(row, ['SKU', 'sku', 'ID', 'id', 'Product ID'])
    raw_images = get_val(row, ['Images', 'images', 'Image URL', 'Image Src'])

    # --- LOGIC MỚI: Tách chuỗi thành List ---
    image_list = []
    if raw_images:
        clean_str = raw_images.replace('\n', ',').replace('\r', '')
        parts = clean_str.split(',')
        for p in parts:
            clean_url = p.strip().strip('"').strip("'")
            if clean_url: 
                image_list.append(clean_url)

    if not image_list: 
        return False, None # Không có ảnh
    
    if not sku: 
        msg = "Error: Missing SKU"
        db.update_row_status(sheet_id, tab_name, index, msg)
        return False, f"Row {index}: Has image but missing SKU."

    # Payload bây giờ chứa mảng "images"
    payload = { "sku": sku, "images": image_list }
    
    res = woo.post_product_image(api_domain, secret, payload)
    
    if res and res.status_code == 200:
        count_img = len(image_list)
        db.update_row_status(sheet_id, tab_name, index, "Done")
        return True, f"Row {index}: Success ({count_img} imgs) - SKU: {sku}"
        
    elif res and res.status_code == 404:
        msg = "Error 404 (Check SKU)"
        db.update_row_status(sheet_id, tab_name, index, msg)
        return False, f"Row {index}: {msg}"
        
    elif res:
        msg = f"PHP Error {res.status_code}: {res.text[:50]}"
        db.update_row_status(sheet_id, tab_name, index, msg)
        return False, f"Row {index}: {msg}"
        
    else:
        db.update_row_status(sheet_id, tab_name, index, "Connection Timeout")
        return False, f"Row {index}: Connection Timeout"

# --- MANAGER FUNCTION ---
def process_import(data_rows, domain, secret, mode, sheet_id, tab_name, max_workers=4, progress_callback=None):
    logs = []
    total_items = len(data_rows)
    count_ok = 0
    count_fail = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i, row in enumerate(data_rows):
            real_row_idx = i + 2 
            
            if mode == 'data':
                futures.append(executor.submit(worker_import_data, row, domain, secret, real_row_idx, sheet_id, tab_name))
            else:
                futures.append(executor.submit(worker_import_image, row, domain, secret, real_row_idx, sheet_id, tab_name))
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            if progress_callback:
                progress_callback((i + 1) / total_items, i + 1, total_items)
            
            is_ok, msg = future.result()
            if msg:
                if is_ok: count_ok += 1
                else:
                    count_fail += 1
                    logs.append(msg)
                    
    logs.append(f"SUMMARY: Success {count_ok} | Failed {count_fail}")
    return logs