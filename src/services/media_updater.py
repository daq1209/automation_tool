import re
from typing import List, Dict, Optional, Set
from src.repositories import woo, db
from src.utils.common import col_idx_to_letter
from src.utils.logger import logger

# Last Updated: Force Cache Flush

def extract_attachment_id(permalink: str) -> Optional[str]:
    """
    Extract attachment_id from WordPress permalink
    Example: https://site.com/?attachment_id=163052 -> "163052"
    """
    match = re.search(r'attachment_id=(\d+)', permalink)
    return match.group(1) if match else None

def extract_slug_from_url(url: str) -> Optional[str]:
    """
    Extract slug from media URL
    Example: https://site.com/wp-content/uploads/2026/01/image-name.png -> "image-name"
    """
    match = re.search(r'/([^/]+)\.(jpg|jpeg|png|gif|webp)$', url, re.IGNORECASE)
    return match.group(1) if match else None

def fetch_all_media(domain: str, secret: str, limit: int = 200) -> List[Dict]:
    """
    Fetch all media from WordPress and extract IDs + slugs
    Returns: [{"media_id": "163052", "slug": "image-name", "url": "...", "title": "..."}, ...]
    """
    media_list = woo.fetch_media_preview_custom(domain, secret, limit, None)
    if not media_list:
        return []
    
    result = []
    for media in media_list:
        media_id = str(media.get('id', ''))
        if not media_id or media_id == '0':
            media_id = extract_attachment_id(media.get('permalink', ''))
        
        slug = extract_slug_from_url(media.get('url', ''))
        
        if media_id:
            result.append({
                'media_id': media_id,
                'slug': slug or '',
                'url': media.get('url', ''),
                'title': media.get('title', ''),
                'permalink': media.get('permalink', '')
            })
    
    return result

def sync_media_to_sheet(sheet_id: str, tab_name: str, media_data: List[Dict]) -> Dict:
    """
    Sync media data to Google Sheet
    
    Logic:
    - Match by ID or old_slug
    - If found: update fields, set check_update status
    - If not found: create new row
    
    Status logic:
    - "Done": slug matches slug_new
    - "holding": slug still matches old_slug
    - "error": no match found
    """
    gc = db.init_google_sheets()
    if not gc:
        return {"error": "Failed to connect to Google Sheets"}
    
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        vals = ws.get_all_values()
        
        if len(vals) < 1:
            return {"error": "Sheet is empty"}
        
        header = [str(x).strip().lower() for x in vals[0]]
        rows = vals[1:]
        
        # Normalize headers: lowercase, strip, replace space with underscore
        col_map = {}
        for i, h in enumerate(header):
            if h:
                norm_h = h.lower().strip().replace(' ', '_')
                col_map[norm_h] = i
                # Keep original too just in case
                col_map[h] = i
        
        # Required columns
        id_col = col_map.get('id') or col_map.get('image_id') or col_map.get('product_id')
        old_slug_col = col_map.get('old_slug') or col_map.get('slug') or col_map.get('slug_old')
        new_slug_col = col_map.get('slug_new') or col_map.get('new_slug')
        check_col = col_map.get('check_update') or col_map.get('status') or col_map.get('update_status')
        name_new_col = col_map.get('name_new') or col_map.get('new_name') or col_map.get('title_new')
        
        # ... (rest of the function)

        # Mapping verification for Debug
        mapped_cols = {
            "ID": id_col,
            "Old_Slug": old_slug_col,
            "New_Slug": new_slug_col,
            "Check_Update": check_col,
            "New_Name": name_new_col
        }

        # Process each media item
        for media in media_data:
            media_id = media['media_id']
            slug = media['slug']
            
            # Try to find existing row
            row_num = None
            existing_row = None
            
            if media_id in sheet_data:
                row_num, existing_row = sheet_data[media_id]
            elif slug in sheet_data:
                row_num, existing_row = sheet_data[slug]
            
            if row_num:
                # Update existing row logic
                updates_needed = False
                
                # Check status
                # Check status
                current_slug = str(existing_row[old_slug_col]).strip() if old_slug_col is not None and old_slug_col < len(existing_row) else ''
                new_slug_val = str(existing_row[new_slug_col]).strip() if new_slug_col is not None and new_slug_col < len(existing_row) else ''
                
                # Check Title (Name New)
                name_new_val = str(existing_row[name_new_col]).strip() if name_new_col is not None and name_new_col < len(existing_row) else ''
                current_wp_title = str(media.get('title', '')).strip()
                
                # Logic: Done = Title matches New Name AND Slug matches New Slug
                # Logic: Holding = Slug matches Old Slug (Title might not be updated yet)
                # Logic: Error = Anything else (Inconsistent state)
                
                status = "Error" # Default
                
                if name_new_val and new_slug_val:
                    if slug == new_slug_val and current_wp_title == name_new_val:
                        status = "Done"
                    elif slug == current_slug:
                        status = "Holding"
                    else:
                        status = "Error"
                elif slug == current_slug:
                     status = "Holding"

                # Add status update to batch
                if check_col is not None:
                    batch_updates.append({
                        'range': f"{col_idx_to_letter(check_col)}{row_num}",
                        'values': [[status]]
                    })
                    updates_needed = True

                # Update Image ID if empty
                if id_col is not None:
                    current_id = existing_row[id_col] if id_col < len(existing_row) else ''
                    if not current_id:
                        batch_updates.append({
                            'range': f"{col_idx_to_letter(id_col)}{row_num}",
                            'values': [[media_id]]
                        })
                        updates_needed = True

                # [NEW] Check and update Old Slug if matching by ID (Force Sync)
                if old_slug_col is not None:
                     current_slug = existing_row[old_slug_col] if old_slug_col < len(existing_row) else ''
                     
                     # Force update if Sheet slug is different from WP slug (Correct the data)
                     if current_slug != slug: 
                        batch_updates.append({
                            'range': f"{col_idx_to_letter(old_slug_col)}{row_num}",
                            'values': [[slug]]
                        })
                # [NEW] Check name_new to update Title in WordPress
                if name_new_col is not None:
                     new_name_val = str(existing_row[name_new_col]).strip() if name_new_col < len(existing_row) else ''
                     current_wp_title = media.get('title', '')
                     
                     # Calculate target_slug immediately
                     target_slug = ''
                     if new_name_val:
                         target_slug = re.sub(r'[^a-z0-9]+', '-', new_name_val.lower()).strip('-')
                         
                         # [NEW] specific request: Update slug_new column in Sheet first
                         if new_slug_col is not None:
                             current_sheet_slug_new = str(existing_row[new_slug_col]).strip() if new_slug_col < len(existing_row) else ''
                             if current_sheet_slug_new != target_slug:
                                 batch_updates.append({
                                     'range': f"{col_idx_to_letter(new_slug_col)}{row_num}",
                                     'values': [[target_slug]]
                                 })
                                 updates_needed = True

                     if new_name_val and (new_name_val != current_wp_title or (target_slug and target_slug != slug)):
                         # Append to queue for WP Update
                         if 'target_slug' not in locals(): # Regenerate if not done above
                             target_slug = re.sub(r'[^a-z0-9]+', '-', new_name_val.lower()).strip('-')
                             
                         wp_updates.append({
                             'id': media_id, 
                             'title': new_name_val,
                             'slug': target_slug,  # New Slug for WP
                             'old_title': current_wp_title,
                             'old_slug': slug
                         })
                             
                         wp_updates.append({
                             'id': media_id, 
                             'title': new_name_val,
                             'slug': target_slug,  # New Slug for WP
                             'old_title': current_wp_title,
                             'old_slug': slug
                         })
                     elif new_name_val and len(trace_logs) < 5:
                         trace_logs.append(f"Row {media_id}: Equal, No WP Update. '{new_name_val}' == '{current_wp_title}'")

                if updates_needed: updated_count += 1
            else:
                # Prepare new row
                new_row = [''] * len(header)
                if id_col is not None: new_row[id_col] = media_id
                if old_slug_col is not None: new_row[old_slug_col] = slug
                if check_col is not None: new_row[check_col] = "holding"
                new_rows_data.append(new_row)
                created_count += 1
        
        # Execute Batch Operations
        if batch_updates:
            db.update_sheet_batch(sheet_id, tab_name, batch_updates)
            
        if new_rows_data:
            ws.append_rows(new_rows_data)
            
        return {
            "success": True,
            "updated": updated_count,
            "created": created_count,
            "total": len(media_data),
            "wp_updates_queued": wp_updates,
            "debug_info": {
                "columns_found_raw": list(col_map.keys()),
                "mapped_columns_indices": mapped_cols
            }
        }
        
    except Exception as e:
        logger.error(f"Error syncing media to sheet: {e}", exc_info=True)
        return {"error": str(e)}

def execute_wp_updates(domain: str, secret: str, updates: List[Dict], chunk_size: int = 50) -> Dict:
    """
    Execute batch updates to WordPress
    Result format: {"updated_count": 0, "errors": [], "logs": []}
    """
    total_updated = 0
    logs = []
    
    if not updates:
        return {"updated_count": 0, "logs": []}

    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i + chunk_size]
        # Clean payload
        clean_chunk = [{'id': x['id'], 'title': x['title'], 'slug': x.get('slug')} for x in chunk]
        
        res = woo.update_media_batch_custom(domain, secret, clean_chunk)
        
        if res.get('status') == 'success':
            cnt = res.get('updated_count', 0)
            total_updated += cnt
            if res.get('details'):
                first = res['details'][0]
                logs.append(f"Batch {i//chunk_size + 1}: Success ({cnt} items). Sample: {first.get('msg')}")
        else:
            logs.append(f"Batch {i//chunk_size + 1}: Failed - {res}")
            
    return {"updated_count": total_updated, "logs": logs}
