import streamlit as st
import pandas as pd
from src.repositories import db
from src.services import updater
from src.utils.common import render_lock_screen, remove_lock_screen

def render_updater_ui(selected_site):
    st.markdown("## CSV Data Updater")
    st.info(f"Target: **{selected_site['site_name']}** | Sheet ID: `{selected_site['google_sheet_id']}`")
    
    # 1. Configuration Check
    col1, col2 = st.columns([1, 2])
    with col1:
        tab_name = st.text_input("Target Sheet Tab Name:", value="Action")
    with col2:
        uploaded_file = st.file_uploader("Upload CSV Update File", type=['csv'])

    if not uploaded_file:
        st.info("Please upload a CSV file to start.")
        return

    # 2. Load CSV & Review Data
    try:
        if 'df_cache' not in st.session_state or st.session_state.get('last_uploaded') != uploaded_file.name:
            df_raw = pd.read_csv(uploaded_file).fillna("")
            df_raw.insert(0, "Select", False) # Default Unchecked
            st.session_state['df_cache'] = df_raw
            st.session_state['last_uploaded'] = uploaded_file.name
        
        st.subheader("1. Review & Select Data")
        
        # 1A. Column Selection (Simulating "Checkboxes above columns")
        csv_headers_raw = list(st.session_state['df_cache'].columns)
        # Remove 'Select' if it exists in raw (it shouldn't yet in raw, but just safety)
        csv_headers_pure = [h for h in csv_headers_raw if h != 'Select']
        
        st.caption("Step 1: Choose Columns to Update")
        cols_to_update = st.multiselect(
            "Select Columns to Update:", 
            options=csv_headers_pure,
            default=[],
            placeholder="Choose columns..."
        )
        
        st.caption("Step 2: Check Rows to Process (See Highlighted Preview below)")
        
        # Row Selection Controls
        c_btn1, c_btn2, c_space = st.columns([1, 1, 4])
        with c_btn1:
            if st.button("✅ Select All Rows", use_container_width=True):
                st.session_state['df_cache']['Select'] = True
                st.rerun()
        with c_btn2:
            if st.button("❌ Deselect All", use_container_width=True):
                st.session_state['df_cache']['Select'] = False
                st.rerun()

        # 1B. Row Selection (Data Editor)
        st.markdown("##### 📋 Data from CSV File")
        df_editor = st.data_editor(
            st.session_state['df_cache'],
            hide_index=True,
            use_container_width=True,
            column_config={"Select": st.column_config.CheckboxColumn(required=True, width="small")}
        )
        
        # Filter Logic
        df_selected = df_editor[df_editor["Select"] == True]
        
        # 1C. Visual Highlighting (The "Spot Difference" Request)
        if cols_to_update and not df_selected.empty:
            st.markdown("##### 🔍 Highlighted Preview (Values to be Updated)")
            st.caption("Values to be updated are highlighted below:")
            
            # Create a view for styling
            # We want to show the rows that are selected, and highlight the columns that are selected
            style_view = df_editor.copy()
            
            def highlight_cells(data):
                # Data is a Series (Column)
                # If this column is in cols_to_update, highlight True rows
                
                # Check if this column is one of the selected ones (exclude Select col)
                if data.name in cols_to_update:
                    # Return background color for rows where 'Select' is True
                    # Since 'data' aligns with 'style_view', we can use style_view['Select'] mask
                    return ['background-color: #fff9c4; color: black; font-weight: bold' if style_view.loc[idx, 'Select'] else '' for idx in data.index]
                return ['' for _ in data.index]

            st.dataframe(
                style_view.style.apply(highlight_cells, axis=0), 
                use_container_width=True,
                hide_index=True
            )
            
        csv_headers = [c for c in df_editor.columns if c != "Select"]
        
        st.write(f"Processing: **{len(df_selected)} rows** across **{len(cols_to_update)} columns**.")
        if len(df_selected) == 0:
            st.info(" Please select at least one row above.")

    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        return

    # 3. Fetch Sheet Headers
    sheet_headers = []
    if 'sheet_headers_cache' not in st.session_state: st.session_state['sheet_headers_cache'] = {}
    
    # Cache Key: SheetID + TabName
    cache_key = f"{selected_site['google_sheet_id']}_{tab_name}"
    
    with st.container(border=True):
        st.markdown("#### Mapping Configuration")
        c_fetch, c_keys = st.columns([1, 3])
        
        with c_fetch:
            # Button to fetch/refresh headers
            if st.button("Fetch/Refresh Sheet Headers", use_container_width=True):
                try:
                    with st.spinner("Fetching headers from Google Sheet..."):
                        gc = db.init_google_sheets()
                        sh = gc.open_by_key(selected_site['google_sheet_id'])
                        ws = sh.worksheet(tab_name)
                        headers = ws.row_values(1)
                        if headers:
                            st.session_state['sheet_headers_cache'][cache_key] = headers
                            st.success(f"Found {len(headers)} columns.")
                        else:
                            st.error("Tab is empty!")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        # Load from cache if available
        sheet_headers = st.session_state['sheet_headers_cache'].get(cache_key, [])
        
        if not sheet_headers:
            st.warning("Click 'Fetch Sheet Headers' to enable mapping.")
            return

        with c_keys:
            c1, c2 = st.columns(2)
            with c1:
                # Attempt to default to 'ID' or 'SKU_Sheet'
                def_idx_s = 0
                # Fallback if sheet_headers is empty or None
                safe_headers = sheet_headers if sheet_headers else [""]
                
                for idx, h in enumerate(safe_headers):
                    if h and h.lower() in ['id', 'sku', 'product id']:
                        def_idx_s = idx
                        break
                sheet_key = st.selectbox("Sheet Key Column:", safe_headers, index=def_idx_s)
                
            with c2:
                # Attempt to default to 'id' or 'sku_csv'
                def_idx_c = 0
                for idx, h in enumerate(csv_headers):
                    if h.lower() in ['id', 'sku', 'product id']:
                        def_idx_c = idx
                        break
                csv_key = st.selectbox("CSV Key Column:", csv_headers, index=def_idx_c)

    # 3. Column Mapping
    st.subheader("2. Map Columns")
    st.caption("Confirm mapping for selected columns.")
    
    # Auto-guess mapping based on same names
    mapping_data = []
    
    # Get sample row
    sample_row = df_selected.iloc[0] if not df_selected.empty else (st.session_state['df_cache'].iloc[0] if not st.session_state['df_cache'].empty else {})

    for c_col in csv_headers: # Iterate only actual data columns
        # Try to find match in sheet headers
        match_s = next((h for h in sheet_headers if h.lower() == c_col.lower()), "")
        is_key = (c_col.lower() == csv_key.lower())
        
        # Determine current sample val
        ex_val = str(sample_row.get(c_col, '')) if not isinstance(sample_row, dict) else ""
        if len(ex_val) > 50: ex_val = ex_val[:47] + "..."
        
        # Default True if in cols_to_update
        should_update = (c_col in cols_to_update)
        
        mapping_data.append({
            "Update?": should_update, 
            "CSV Column": c_col,
            "Example Value": ex_val,
            "Target Sheet Column": match_s if match_s else c_col # Default to same name
        })
    
    mapping_df = pd.DataFrame(mapping_data)
    edited_mapping = st.data_editor(
        mapping_df, 
        column_config={
            "Update?": st.column_config.CheckboxColumn(help="Check to update this column"),
            "Target Sheet Column": st.column_config.TextColumn(help="Exact header name in Google Sheet")
        },
        disabled=["CSV Column", "Example Value"],
        use_container_width=True,
        hide_index=True
    )
    
    # 4. Process Mapping
    final_mapping = {} # {csv_col: sheet_col}
    for index, row in edited_mapping.iterrows():
        if row["Update?"] and row["Target Sheet Column"]:
            final_mapping[row["CSV Column"]] = row["Target Sheet Column"]
            
    if not final_mapping:
        st.warning("Please select at least one column to update.")
        return
        
    # 5. Preview Button
    st.subheader("2. Preview Changes")
    if st.button("Generate Preview"):
        with st.spinner("Fetching Sheet Data & Comparing..."):
            try:
                # Fetch Sheet Data
                gc = db.init_google_sheets()
                sh = gc.open_by_key(selected_site['google_sheet_id'])
                ws = sh.worksheet(tab_name)
                vals = ws.get_all_values()
                
                if len(vals) < 2:
                    st.error("Sheet is empty!")
                    return
                
                # Parse Sheet Data
                header = vals[0]
                rows = []
                for i, r in enumerate(vals[1:]):
                    row_dict = {h: val for h, val in zip(header, r + [""] * (len(header) - len(r)))}
                    row_dict['_real_row'] = i + 2
                    rows.append(row_dict)
                
                # Calculate Diff
                preview_list, stats = updater.process_csv_update_preview(
                    rows, df_selected, sheet_key, csv_key, final_mapping
                )
                
                st.session_state['updater_preview'] = preview_list
                st.session_state['updater_stats'] = stats
                st.session_state['updater_headers'] = header # Save headers for execution
                
            except Exception as e:
                st.error(f"Error generating preview: {e}")

    # 6. Render Preview Result
    if 'updater_preview' in st.session_state and st.session_state.get('updater_preview'):
        stats = st.session_state['updater_stats']
        st.success(f"Matched Rows: {stats['matched_rows']} | Unmatched: {stats['unmatched_rows']} | Cells to Change: {stats['cells_to_update']}")
        
        st.markdown("##### 📊 Update Preview (Google Sheet vs CSV)")
        preview_df = pd.DataFrame(st.session_state['updater_preview'])
        
        # Highlight Diffs
        def highlight_diff(data):
            attr = 'background-color: #ffcdd2; color: black' # Red for Old
            attr2 = 'background-color: #c8e6c9; color: black' # Green for New
            if data.name == 'Old Value':
                return [attr] * len(data)
            if data.name == 'New Value':
                return [attr2] * len(data)
            return [''] * len(data)

        st.dataframe(preview_df.style.apply(highlight_diff, axis=0), use_container_width=True)
        
        # 7. Execute Button
        st.subheader("3. Apply Updates")
        st.warning("This action will modify your Google Sheet directly. Please verify the preview above.")
        
        if st.button("CONFIRM UPDATE", type="primary"):
            lock = st.empty()
            with lock: render_lock_screen()
            try:
                success = updater.execute_batch_update(
                    selected_site['google_sheet_id'], 
                    tab_name, 
                    st.session_state['updater_preview'],
                    st.session_state['updater_headers']
                )
                
                if success:
                    st.toast("Update Successful!")
                    st.success("Google Sheet has been updated successfully.")
                    # Clear state
                    del st.session_state['updater_preview']
                else:
                    st.error("Failed to update.")
            except Exception as e:
                st.error(f"Execution Error: {e}")
            finally:
                with lock: remove_lock_screen()
    elif 'updater_preview' in st.session_state:
        st.info("No changes detected. Check your keys and data.")
