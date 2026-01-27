import pandas as pd
from src.services.updater import process_csv_update_preview

def test_logic():
    print("=== Testing Data Updater Logic ===")
    
    # 1. Mock Sheet Data
    sheet_data = [
        {'_real_row': 2, 'ID': 'SKU_001', 'Price': '100', 'Title': 'Shirt'},
        {'_real_row': 3, 'ID': 'SKU_002', 'Price': '200', 'Title': 'Pant'},
        {'_real_row': 4, 'ID': 'SKU_003', 'Price': '300', 'Title': 'Hat'},
    ]
    print(f"Sheet Data: {len(sheet_data)} rows")

    # 2. Mock CSV Data (Pandas DataFrame)
    csv_data = pd.DataFrame([
        {'sku': 'SKU_001', 'new_price': 150},       # Update Price
        {'sku': 'SKU_002', 'new_price': 200},       # No Change
        {'sku': 'SKU_004', 'new_price': 500},       # New Item (Should be ignored)
    ])
    print(f"CSV Data: {len(csv_data)} rows")
    
    # 3. Define Mapping
    # CSV 'sku' -> Sheet 'ID'
    # CSV 'new_price' -> Sheet 'Price'
    sheet_key = 'ID'
    csv_key = 'sku'
    col_mapping = {'new_price': 'Price'}
    
    # 4. Run Function
    print("\nRunning comparison...")
    preview, stats = process_csv_update_preview(
        sheet_data, csv_data, sheet_key, csv_key, col_mapping
    )
    
    # 5. Verify Results
    print(f"\nStats: {stats}")
    print("\nPreview Changes:")
    for p in preview:
        print(p)
        
    # Assertions
    # Expected: SKU_001 changes Price 100 -> 150
    # SKU_002 matches but no change
    # SKU_004 unmatched
    
    assert stats['matched_rows'] == 2
    assert stats['unmatched_rows'] == 1
    assert stats['cells_to_update'] == 1
    
    change = preview[0]
    assert change['Key'] == 'SKU_001'
    assert change['Old Value'] == '100'
    assert change['New Value'] == '150'
    
    print("\n✅ TEST PASSED: Logic is correct.")

if __name__ == "__main__":
    try:
        test_logic()
    except AssertionError as e:
        print("❌ TEST FAILED: Assertion Error")
        raise
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        raise
