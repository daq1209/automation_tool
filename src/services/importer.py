import concurrent.futures
import time
from src.repositories import woo, db
from src.utils.common import get_val, col_idx_to_letter
from config import Config
from src.utils.logger import logger

# --- PHASE 1: BATCH TEXT PROCESSING ---
def worker_import_batch_v12(rows_chunk, domain, secret, pub_col_letter):
    payload_list = []
    sku_map = {} 

    for row in rows_chunk:
        sheet_id_val = get_val(row, ['ID', 'id', 'Product ID'])
        sheet_sku_val = get_val(row, ['SKU', 'sku', 'Model'])
        final_sku = sheet_id_val if sheet_id_val else sheet_sku_val
        if not final_sku: continue

        # Extract images
        raw_images = get_val(row, ['Images', 'images', 'Image URL'])
        image_list = []
        if raw_images:
            parts = raw_images.replace('\n', ',').replace('\r', '').split(',')
            image_list = [p.strip().strip('"') for p in parts if p.strip()]

        payload_list.append({
            "sku": final_sku,
            "title": get_val(row, ['Name', 'Title', 'title']),
            "price": get_val(row, ['Regular price', 'Price']),
            "description": get_val(row, ['Description', 'description']),
            "images": image_list
        })
        sku_map[final_sku] = row.get('_real_row')

    if not payload_list: return []

    # Send Batch API
    res = woo.post_product_batch_v12(domain, secret, payload_list)
    
    updates = []
    if res and res.status_code == 200:
        data = res.json().get('results', [])
        for item in data:
            sku = item.get('sku')
            status = item.get('status')
            row_idx = sku_map.get(sku)
            if row_idx:
                if status == 'success':
                    # [RULE 2] SUCCESS -> Done | 1
                    updates.append({'range': f'A{row_idx}', 'values': [['Done']]})
                    if pub_col_letter:
                        updates.append({'range': f'{pub_col_letter}{row_idx}', 'values': [[1]]})
                else:
                    updates.append({'range': f'A{row_idx}', 'values': [[f"Error: {item.get('message')}"]]})
    else:
        err = f"Error {res.status_code}" if res else "Conn Error"
        for p in payload_list:
            r = sku_map.get(p['sku'])
            if r: updates.append({'range': f'A{r}', 'values': [[err]]})
    return updates

# --- PHASE 2: WORKER TRIGGER ---
def worker_trigger_loop(domain, secret):
    processed_count = 0
    consecutive_empty = 0
    while True:
        res = woo.trigger_process_media(domain, secret, limit=1)
        if res and res.get('status') == 'processing':
            processed_count += res.get('processed_count', 0)
            consecutive_empty = 0
            time.sleep(Config.PHASE_DELAY)
        elif res and res.get('status') == 'done':
            consecutive_empty += 1
            if consecutive_empty > 2: break 
            time.sleep(Config.WORKER_COMPLETION_DELAY)
        else:
            consecutive_empty += 1
            if consecutive_empty > 5: break
            time.sleep(5)
    return processed_count

# --- MAIN CONTROLLER ---
def process_import(data_rows, domain, secret, mode, sheet_id, tab_name, max_workers=15, progress_callback=None):
    logs = []
    batch_updates = []
    
    if mode == 'data':
        # Find Published Column
        pub_col_letter = None
        if data_rows:
            headers = list(data_rows[0].keys())
            for i, h in enumerate(headers):
                if h.lower().strip() in ['published', 'active', 'is_published']:
                    pub_col_letter = col_idx_to_letter(i)
                    break
        
        logs.append(f"=== PHASE 1: DATA IMPORT (Pub Col: {pub_col_letter}) ===")
        
        chunk_size = Config.CHUNK_SIZE
        chunks = [data_rows[i:i + chunk_size] for i in range(0, len(data_rows), chunk_size)]
        
        completed_batches = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(worker_import_batch_v12, c, domain, secret, pub_col_letter) for c in chunks]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res: batch_updates.extend(res)
                completed_batches += 1
                if progress_callback: progress_callback(completed_batches / len(chunks) * 0.1, completed_batches, len(chunks))

        if batch_updates:
            db.update_sheet_batch(sheet_id, tab_name, batch_updates)
            logs.append("Phase 1 Done. Data uploaded. Sheet updated (Done | 1).")

        # PHASE 2
        logs.append("=== PHASE 2: BACKGROUND IMAGE DOWNLOADING ===")
        logs.append(f"Launching {max_workers} Workers...")
        
        total_processed_imgs = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_trigger_loop, domain, secret) for _ in range(max_workers)]
            for future in concurrent.futures.as_completed(futures):
                total_processed_imgs += future.result()
                if progress_callback: progress_callback(1.0, total_processed_imgs, len(data_rows))

        logs.append("=== ALL PHASES COMPLETED ===")
    return logs