import concurrent.futures
from src.repositories import woo, db
from src.utils.common import get_val, col_idx_to_letter

# --- WORKERS ---
def worker_delete_product(ids_chunk, domain, secret):
    success, count, deleted_skus = woo.delete_products_batch_custom(domain, secret, ids_chunk)
    return success, count, (deleted_skus if success else [])

def worker_fetch_page(page, domain, ck, cs):
    res = woo.fetch_product_ids_page(domain, ck, cs, page, status='publish')
    return [p['id'] for p in res.json()] if res and res.status_code == 200 else []

# --- UI FETCHERS (Same as before) ---
def get_products_for_ui(domain, secret, limit=50, search_input=None):
    search_term = None
    if search_input:
        search_term = ",".join(search_input) if isinstance(search_input, list) else str(search_input).strip()
    raw_data = woo.fetch_product_list_custom(domain, secret, limit, search_term)
    if not raw_data: return []
    clean_data = []
    for p in raw_data:
        clean_data.append({"Select": False, "ID": p['id'], "Image": p['image'], "Name": p['name'], "SKU": p['sku'], "Status": p['status']})
    return clean_data

def get_media_for_ui(domain, secret, limit=50, search_input=None):
    # (Same as previous versions)
    search_term = None
    if search_input:
        search_term = ",".join(search_input) if isinstance(search_input, list) else str(search_input).strip()
    raw_data = woo.fetch_media_preview_custom(domain, secret, limit, search_term)
    if not raw_data: return []
    clean_data = []
    for m in raw_data:
        clean_data.append({"Select": False, "ID": m['id'], "Thumbnail": m['url'], "Date": m['date']})
    return clean_data

# --- DELETE LOGIC ---
def delete_product_list(domain, secret, id_list, max_workers=5, progress_callback=None):
    if not id_list: return ["List empty"], []
    chunk_size = 50 
    chunks = [id_list[i:i + chunk_size] for i in range(0, len(id_list), chunk_size)]
    deleted_total = 0
    returned_skus = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker_delete_product, chunk, domain, secret) for chunk in chunks]
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            is_ok, count, skus = future.result()
            if is_ok: 
                deleted_total += count
                returned_skus.extend(skus)
            if progress_callback: 
                progress_callback((i + 1) / len(chunks), deleted_total, len(id_list))
                
    return [f"Deleted {deleted_total} items."], returned_skus

def delete_all_products_scan_mode(domain, ck, cs, secret, max_workers=10, progress_callback=None):
    res1 = woo.fetch_product_ids_page(domain, ck, cs, 1, status='publish')
    if not res1 or res1.status_code != 200: return ["Connect Fail"], []
    total_pages = int(res1.headers.get('X-WP-TotalPages', 0))
    all_ids = [p['id'] for p in res1.json()]
    if total_pages > 1:
        pages = list(range(2, total_pages + 1))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_fetch_page, p, domain, ck, cs) for p in pages]
            for f in concurrent.futures.as_completed(futures):
                all_ids.extend(f.result())
    if not all_ids: return ["No products found."], []
    return delete_product_list(domain, secret, all_ids, max_workers, progress_callback)

def sync_deleted_rows(sheet_id, tab_name, deleted_skus):
    """
    [RULE 3] DELETE SUCCESS -> Holding | -1
    """
    if not deleted_skus: return ["No items to sync."]
    gc = db.init_google_sheets()
    if not gc: return ["Connection Error"]
    
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        vals = ws.get_all_values()
        if len(vals) < 2: return ["Sheet empty"]
        header = [str(x).strip() for x in vals[0]]
        data = vals[1:]
        
        id_col_indices = [i for i, h in enumerate(header) if h.lower() in ['sku', 'id', 'product id']]
        if not id_col_indices: return ["No ID/SKU column found"]
        id_col_idx = id_col_indices[0]
        
        pub_col_letter = None
        for i, h in enumerate(header):
            if h.lower() in ['published', 'active', 'is_published']:
                pub_col_letter = col_idx_to_letter(i)
                break

        batch_updates = []
        count = 0
        deleted_set = {str(x).strip() for x in deleted_skus}
        
        for i, row in enumerate(data):
            if len(row) > id_col_idx:
                current_sheet_val = str(row[id_col_idx]).strip()
                if current_sheet_val in deleted_set:
                    row_num = i + 2
                    # Status -> Holding
                    batch_updates.append({'range': f'A{row_num}','values': [['Holding']]})
                    # Published -> -1
                    if pub_col_letter:
                        batch_updates.append({'range': f'{pub_col_letter}{row_num}','values': [[-1]]})
                    count += 1
                    
        if batch_updates: 
            db.update_sheet_batch(sheet_id, tab_name, batch_updates)
            return [f"Synced {count} rows to 'Holding' / '-1'."]
        return [f"Deleted {len(deleted_skus)} items from WP (No match in sheet)."]
        
    except Exception as e: return [f"Sync Error: {str(e)}"]

def delete_all_media(domain, secret, max_workers=10, progress_callback=None):
    # (Same as before)
    all_ids = woo.get_all_media_ids(domain, secret)
    total = len(all_ids)
    if total == 0: return True, "Empty Library"
    chunks = [all_ids[i:i + 50] for i in range(0, total, 50)]
    deleted = 0
    def worker(chunk, dom, sec):
        res = woo.delete_media_batch(dom, sec, chunk)
        return res, len(chunk)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(worker, c, domain, secret) for c in chunks]
        for f in concurrent.futures.as_completed(futures):
            ok, n = f.result()
            if ok: deleted += n
            if progress_callback: progress_callback(1, deleted, total)
    return True, f"Deleted {deleted} images."