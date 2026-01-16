from src.repositories import woo, db
from src.utils.common import get_val, col_idx_to_letter

def run_sync_sheet_with_website(site, tab_name, max_workers=20, progress_callback=None):
    """
    V12.3: FAST SYNC ALGORITHM
    1. Fetch ALL SKUs from WP in 1 request.
    2. Compare with Sheet Data in Memory.
    3. Batch Update missing items.
    """
    gc = db.init_google_sheets()
    if not gc: return ["Connection Error"]
    
    try:
        # 1. Fetch WP SKUs (Speed: ~2s for 10k items)
        if progress_callback: progress_callback(0.1)
        wp_sku_set = woo.get_all_skus_fast(site['domain_url'], site['secret_key'])
        
        # 2. Fetch Sheet Data
        sh = gc.open_by_key(site['google_sheet_id'])
        ws = sh.worksheet(tab_name)
        vals = ws.get_all_values()
        
        if len(vals) < 2: return ["Sheet is empty"]
        
        header = [str(x).strip() for x in vals[0]]
        data = vals[1:]
        
        # Find Published Column
        pub_col_letter = None
        for i, h in enumerate(header):
            if h.lower() in ['published', 'active', 'is_published']:
                pub_col_letter = col_idx_to_letter(i)
                break
        
        # Find ID/SKU Column indices
        id_keys = ['id', 'product id']
        sku_keys = ['sku', 'model']
        
        id_idx = next((i for i, h in enumerate(header) if h.lower() in id_keys), -1)
        sku_idx = next((i for i, h in enumerate(header) if h.lower() in sku_keys), -1)

        batch_updates = []
        count_synced = 0
        total_rows = len(data)
        
        # 3. Memory Comparison (Speed: ~0.1s)
        for i, row in enumerate(data):
            row_num = i + 2
            
            # Get Sheet ID/SKU
            sheet_id = str(row[id_idx]).strip() if id_idx != -1 else ""
            sheet_sku = str(row[sku_idx]).strip() if sku_idx != -1 else ""
            
            # Key logic: Check if Sheet ID OR Sheet SKU exists in WP Set
            exists_on_wp = False
            if sheet_id and sheet_id in wp_sku_set: exists_on_wp = True
            elif sheet_sku and sheet_sku in wp_sku_set: exists_on_wp = True
            
            # Get current status in sheet (Col A)
            current_status = str(row[0]).lower().strip()
            
            # If NOT on WP but Sheet says something else (or empty), force it to Holding
            if not exists_on_wp:
                if 'holding' not in current_status:
                    batch_updates.append({'range': f'A{row_num}', 'values': [['Holding']]})
                    if pub_col_letter:
                        batch_updates.append({'range': f'{pub_col_letter}{row_num}', 'values': [[-1]]})
                    count_synced += 1
            
            if progress_callback and i % 500 == 0: 
                progress_callback(0.2 + (0.8 * (i / total_rows)))

        # 4. Push Updates
        if batch_updates:
            db.update_sheet_batch(site['google_sheet_id'], tab_name, batch_updates)
            if progress_callback: progress_callback(1.0)
            return [f"Fast Sync: Found {count_synced} items missing on WP. Reset to 'Holding'."]
        
        if progress_callback: progress_callback(1.0)
        return [f"Fast Sync: All {total_rows} items checked. Everything matches."]

    except Exception as e:
        return [f"Sync Error: {str(e)}"]