import pandas as pd
from typing import List, Dict, Tuple, Any
from src.repositories import db
from src.utils.common import col_idx_to_letter

def process_csv_update_preview(
    sheet_data: List[Dict[str, Any]], 
    csv_df: pd.DataFrame, 
    sheet_key_col: str, 
    csv_key_col: str, 
    column_mapping: Dict[str, str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Compare Sheet Data vs CSV Data and generate a preview of changes.
    
    Args:
        sheet_data: List of dicts representing Sheet rows (must include '_real_row').
        csv_df: DataFrame of the uploaded CSV.
        sheet_key_col: The column name in Sheet to use as Key (e.g. 'ID').
        csv_key_col: The column name in CSV to use as Key (e.g. 'sku').
        column_mapping: Dict mapping {CSV_Col: Sheet_Col} for columns to update.
        
    Returns:
        preview_rows: List of changes for UI display.
        stats: Summary statistics.
    """
    preview_rows = []
    stats = {
        'total_csv_rows': len(csv_df),
        'matched_rows': 0,
        'unmatched_rows': 0,
        'cells_to_update': 0
    }
    
    # 1. Index Sheet Data by Key for fast lookup
    # Normalize keys to string, stripped, lower for case-insensitive matching
    sheet_map = {}
    for row in sheet_data:
        key_val = str(row.get(sheet_key_col, '')).strip().lower()
        if key_val:
            sheet_map[key_val] = row

    # 2. Iterate CSV and Compare
    for _, csv_row in csv_df.iterrows():
        csv_key_val = str(csv_row.get(csv_key_col, '')).strip().lower()
        
        if not csv_key_val:
            continue
            
        target_row = sheet_map.get(csv_key_val)
        
        if target_row:
            stats['matched_rows'] += 1
            row_changes = False
            
            for csv_col, sheet_col in column_mapping.items():
                if csv_col not in csv_row: continue
                
                # Get Values
                new_val = str(csv_row[csv_col]).strip()
                # Handle NaN/None in CSV
                if pd.isna(csv_row[csv_col]): new_val = ""
                
                old_val = str(target_row.get(sheet_col, '')).strip()
                
                if new_val != old_val:
                    preview_rows.append({
                        "Row": target_row.get('_real_row'),
                        "Key": target_row.get(sheet_key_col), # Show original case
                        "Column": sheet_col,
                        "Old Value": old_val,
                        "New Value": new_val
                    })
                    row_changes = True
                    stats['cells_to_update'] += 1
        else:
            stats['unmatched_rows'] += 1

    return preview_rows, stats

def execute_batch_update(sheet_id: str, tab_name: str, updates: List[Dict[str, Any]], sheet_headers: List[str]) -> bool:
    """
    Execute the changes calculated in preview.
    
    Args:
        sheet_id: Google Sheet ID
        tab_name: Tab Name
        updates: List of preview_row dicts (Row, Column, New Value)
        sheet_headers: List of header names to find column index
    
    Returns:
        bool: Success
    """
    if not updates: return True
    
    # 1. Map Column Names to Letters
    # header_map = {'Name': 'B', 'Price': 'C', ...}
    header_map = {}
    for i, h in enumerate(sheet_headers):
        header_map[h] = col_idx_to_letter(i)
        
    final_updates = []
    
    for item in updates:
        col_name = item['Column']
        row_idx = item['Row']
        new_val = item['New Value']
        
        col_letter = header_map.get(col_name)
        if col_letter:
            range_str = f"{col_letter}{row_idx}"
            final_updates.append({
                'range': range_str,
                'values': [[new_val]]
            })
            
    # 2. Batch Update via DB Repository
    # Split into chunks to avoid API limits if necessary (though db.update_sheet_batch is robust)
    if final_updates:
        # We reuse the existing update_sheet_batch function
        # It takes list of {'range': 'A1', 'values': [['val']]}
        db.update_sheet_batch(sheet_id, tab_name, final_updates)
        return True
        
    return False
