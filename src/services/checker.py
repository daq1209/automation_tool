from src.repositories import woo, db
from src.utils.common import get_val, col_idx_to_letter

def run_sync_sheet_with_website(site, tab_name, max_workers=20, progress_callback=None):
    """
    V12.4 FIXED: TWO-WAY SYNC
    1. Fetch ALL SKUs from WP.
    2. Loop Sheet:
       - IF Exists on WP -> Update Sheet to 'Done' | '1' (If not already).
       - IF Missing on WP -> Update Sheet to 'Holding' | '-1'.
    """
    gc = db.init_google_sheets()
    if not gc: return ["Connection Error"]
    
    try:
        # 1. Fetch WP SKUs
        if progress_callback: progress_callback(0.1)
        # Set này chứa cả ID (str) và SKU (str) từ Web
        wp_sku_set = woo.get_all_skus_fast(site['domain_url'], site['secret_key'])
        
        # 2. Fetch Sheet Data
        sh = gc.open_by_key(site['google_sheet_id'])
        ws = sh.worksheet(tab_name)
        vals = ws.get_all_values()
        
        if len(vals) < 2: return ["Sheet is empty"]
        
        header = [str(x).strip() for x in vals[0]]
        data = vals[1:]
        
        # Identify Columns
        pub_col_letter = None
        pub_col_idx = -1
        for i, h in enumerate(header):
            if h.lower() in ['published', 'active', 'is_published']:
                pub_col_letter = col_idx_to_letter(i)
                pub_col_idx = i
                break
        
        id_keys = ['id', 'product id']
        sku_keys = ['sku', 'model']
        
        id_idx = next((i for i, h in enumerate(header) if h.lower() in id_keys), -1)
        sku_idx = next((i for i, h in enumerate(header) if h.lower() in sku_keys), -1)

        batch_updates = []
        count_synced_done = 0
        count_synced_holding = 0
        total_rows = len(data)
        
        # 3. Logic Sync 2 Chiều
        for i, row in enumerate(data):
            row_num = i + 2
            
            # Lấy giá trị ID/SKU từ Sheet và làm sạch
            # Thêm replace('.0', '') để xử lý trường hợp ID bị Excel format sai (VD: 5520.0)
            sheet_id = str(row[id_idx]).strip().replace('.0', '') if id_idx != -1 and len(row) > id_idx else ""
            sheet_sku = str(row[sku_idx]).strip() if sku_idx != -1 and len(row) > sku_idx else ""
            
            # Check tồn tại
            exists_on_wp = False
            if sheet_id and sheet_id in wp_sku_set: exists_on_wp = True
            elif sheet_sku and sheet_sku in wp_sku_set: exists_on_wp = True
            
            # Lấy trạng thái hiện tại trên Sheet
            current_status = str(row[0]).lower().strip() if len(row) > 0 else ""
            current_pub = str(row[pub_col_idx]).strip() if pub_col_idx != -1 and len(row) > pub_col_idx else ""

            if exists_on_wp:
                # [CASE 1] Có trên Web -> Phải là Done | 1
                need_update = False
                # Nếu chưa là Done -> update
                if 'done' not in current_status: 
                    batch_updates.append({'range': f'A{row_num}', 'values': [['Done']]})
                    need_update = True
                
                # Nếu cột Published tồn tại và chưa là 1 -> update
                if pub_col_letter and current_pub != '1':
                    batch_updates.append({'range': f'{pub_col_letter}{row_num}', 'values': [[1]]})
                    need_update = True
                
                if need_update: count_synced_done += 1

            else:
                # [CASE 2] Không có trên Web -> Phải là Holding | -1
                # Chỉ update nếu nó đang khác Holding (để tránh update dư thừa)
                if 'holding' not in current_status and sheet_id: # Chỉ update nếu có ID/SKU mà ko tìm thấy
                    batch_updates.append({'range': f'A{row_num}', 'values': [['Holding']]})
                    if pub_col_letter:
                        batch_updates.append({'range': f'{pub_col_letter}{row_num}', 'values': [[-1]]})
                    count_synced_holding += 1
            
            if progress_callback and i % 500 == 0: 
                progress_callback(0.2 + (0.8 * (i / total_rows)))

        # 4. Push Updates
        if batch_updates:
            db.update_sheet_batch(site['google_sheet_id'], tab_name, batch_updates)
            msg = f"Sync Complete: Updated {count_synced_done} to 'Done' (Found on WP) & {count_synced_holding} to 'Holding' (Missing)."
            if progress_callback: progress_callback(1.0)
            return [msg]
        
        if progress_callback: progress_callback(1.0)
        return [f"Sync Checked {total_rows} items. Everything matches perfect."]

    except Exception as e:
        return [f"Sync Error: {str(e)}"]