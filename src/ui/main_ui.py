import streamlit as st
import pandas as pd
from datetime import date
from src.repositories import db
from src.services import importer, deleter, checker

# --- CUSTOM CSS ---
def local_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        .stButton button { width: 100%; border-radius: 6px; font-weight: 600; }
        .stSelectbox div[data-baseweb="select"] > div { border-radius: 6px; }
        .stTextInput input { border-radius: 6px; }
        /* Dark Sidebar */
        [data-testid="stSidebar"] { background-color: #2c3e50; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #ecf0f1; }
        
        /* [FIX FINAL] CSS CHO NÚT SELECT ALL / DESELECT ALL */
        div[data-testid="column"] button { 
            white-space: nowrap !important;      /* Cấm xuống dòng */
            min-width: fit-content !important;   /* Ép nút giãn ra bằng chữ */
            width: auto !important;
            padding: 0.4rem 0.8rem !important;
            font-size: 14px !important;
            margin: 0px !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    local_css()

    with st.sidebar:
        st.title("Admin Console")
        st.write("---")
        st.info("System Ready")
        st.write("")
        if st.button("Logout", type="secondary"):
            st.session_state['is_logged_in'] = False
            st.rerun()

    st.title("POD Automation Environment")
    
    sites = db.get_all_sites()
    if not sites:
        st.error("No websites found in database.")
        return

    site_map = {s['site_name']: s for s in sites}
    site_options = ["-- Select a Website --"] + list(site_map.keys())
    
    if 'previous_site' not in st.session_state:
        st.session_state['previous_site'] = site_options[0]

    col_sel, _ = st.columns([2, 1])
    with col_sel:
        selected_option = st.selectbox("Target Website:", site_options, label_visibility="collapsed")

    if selected_option == site_options[0]:
        st.info("Please select a website from the dropdown above to proceed.")
        st.session_state['previous_site'] = site_options[0]
        return

    selected_site = site_map[selected_option]

    if selected_option != st.session_state['previous_site']:
        st.session_state['previous_site'] = selected_option
        run_check_process(selected_site, "Action", 20, is_test=False, is_auto=True)
        if 'prod_preview' in st.session_state: del st.session_state['prod_preview']
        if 'media_preview' in st.session_state: del st.session_state['media_preview']

    st.write("") 

    with st.container(border=True):
        st.markdown("### Settings & Configuration")
        c1, c2, c3 = st.columns(3)
        with c1: default_tab_data = st.text_input("Data Tab Name:", value="Action")
        with c2: default_tab_img = st.text_input("Image Tab Name:", value="Action")
        with c3: auto_threads = st.slider("Performance (Threads):", min_value=1, max_value=50, value=20)

    st.write("") 

    tab1, tab2 = st.tabs(["Import Tool", "Delete Tool"])

    # === TAB 1: IMPORT ===
    with tab1:
        with st.container(border=True):
            st.markdown("#### Import Scope")
            c_mode, c_info, c_test = st.columns([2, 2, 1])
            with c_mode: import_mode = st.radio("Mode:", ["Import All Rows", "Filter by Specific IDs"], horizontal=True)
            filter_ids = []
            if import_mode == "Filter by Specific IDs":
                st.info("Enter IDs present in your Sheet (Column 'ID').")
                txt_filter = st.text_area("Sheet IDs (One per line):", height=100, key="import_filter")
                if txt_filter: filter_ids = [x.strip() for x in txt_filter.replace(',', '\n').split('\n') if x.strip()]
            with c_info: 
                if filter_ids: st.success(f"Targeting {len(filter_ids)} items.")
                else: st.write(f"Active Tab: **{default_tab_data}**")
            with c_test: 
                test_val = False if filter_ids else True
                is_test = st.toggle("Test Mode (5 rows)", value=test_val)
        
        st.write("")
        render_data_preview(selected_site, default_tab_data, is_test, filter_ids)
        st.write("")

        col_step1, col_step2 = st.columns(2)
        with col_step1:
            with st.container(border=True):
                st.markdown("#### Step 1: Text Data")
                st.caption("Auto-detect ID column > SKU.")
                if st.button("Run Import Data", type="primary"):
                    run_import(selected_site, default_tab_data, 'data', is_test, auto_threads, filter_ids)
        with col_step2:
            with st.container(border=True):
                st.markdown("#### Step 2: Images")
                st.caption("Sync Main Image & Gallery")
                if st.button("Run Sync Images", type="secondary"):
                    run_import(selected_site, default_tab_img, 'image', is_test, auto_threads, filter_ids)

    # === TAB 2: DELETE ===
    with tab2:
        render_delete_tool(sites, list(site_map.keys()), selected_option, default_tab_data, auto_threads)

# --- HELPER FUNCTIONS ---
def render_data_preview(site, tab_name, is_test, filter_ids):
    gc = db.init_google_sheets()
    if not gc: return
    sheet_id = site.get('google_sheet_id')
    with st.spinner("Fetching data from Sheet..."):
        try:
            sh = gc.open_by_key(sheet_id)
            ws = sh.worksheet(tab_name)
            vals = ws.get_all_values()
            if len(vals) < 2: return
            header = [str(x).strip() for x in vals[0]]
            data = vals[1:]
            df = pd.DataFrame(data, columns=header)
            
            if filter_ids:
                id_keys = [col for col in df.columns if col.lower() in ['id', 'product id', 'sku']]
                if id_keys:
                    id_key = id_keys[0]
                    target_set = {str(x).strip() for x in filter_ids}
                    df = df[df[id_key].astype(str).str.strip().isin(target_set)]
            
            if is_test and not filter_ids: df = df.head(5)
            
            st.markdown(f"### Data Preview ({len(df)} rows)")
            st.dataframe(df, use_container_width=True, hide_index=True, height=300)
        except: pass

def render_delete_tool(sites, site_names, selected_name, default_tab_data, auto_threads):
    del_site = next((s for s in sites if s['site_name'] == selected_name), None)
    if not del_site: return
    
    ck = del_site.get('consumer_key') or ""
    cs = del_site.get('consumer_secret') or ""
    domain_clean = del_site['domain_url'].replace('https://', '').replace('http://', '').strip('/')

    t_prod, t_media = st.tabs(["Delete Products", "Delete Media"])

    # --- TAB: DELETE PRODUCTS ---
    with t_prod:
        mode_prod = st.radio("Option:", ["Visual Selection (Fetch & Select)", "Wipe All Products"], horizontal=True)
        st.divider()

        if "Visual" in mode_prod:
            c_filter, c_act = st.columns([3, 1])
            with c_filter:
                fetch_ids_input = st.text_input("Filter by IDs (Optional - comma separated):", placeholder="e.g. 20435, 20436")
                limit_prod = st.slider("Or Fetch Latest (Limit):", 10, 200, 50, step=10, key="lim_p")
            with c_act:
                st.write("")
                st.write("")
                if st.button("Fetch Products"):
                    with st.spinner("Fetching from WordPress..."):
                        specific_ids = [x.strip() for x in fetch_ids_input.split(',')] if fetch_ids_input.strip() else None
                        data = deleter.get_products_for_ui(del_site['domain_url'], ck, cs, limit_prod, specific_ids)
                        st.session_state['prod_preview'] = pd.DataFrame(data) if data else pd.DataFrame()

            if 'prod_preview' in st.session_state and not st.session_state['prod_preview'].empty:
                df_p = st.session_state['prod_preview']
                st.caption(f"Found {len(df_p)} items.")
                
                # [FIXED] Tăng tỷ lệ cột lên [2, 2.2] để đủ chỗ cho chữ không bị xuống dòng
                # 12 là khoảng trống spacer lớn để đẩy nút về trái
                c_btn1, c_btn2, _ = st.columns([2, 2.2, 12], gap="small")
                
                if c_btn1.button("Select All", key="sel_all_p"):
                    st.session_state['prod_preview']['Select'] = True
                    st.rerun()
                if c_btn2.button("Deselect All", key="desel_all_p"):
                    st.session_state['prod_preview']['Select'] = False
                    st.rerun()
                
                edited_df = st.data_editor(
                    st.session_state['prod_preview'],
                    key="prod_editor", 
                    use_container_width=True, 
                    height=450, 
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", default=False),
                        "Image": st.column_config.ImageColumn("Img", width="small"),
                        "ID": st.column_config.TextColumn("ID", disabled=True),
                    }
                )
                
                selected_rows = edited_df[edited_df["Select"] == True]
                count_sel = len(selected_rows)
                st.write("")
                if st.button(f"DELETE {count_sel} SELECTED PRODUCTS", type="primary", disabled=(count_sel==0)):
                    ids_to_del = selected_rows["ID"].astype(str).tolist()
                    run_delete_products(del_site, ck, cs, ids_to_del, auto_threads, False, default_tab_data)
                    del st.session_state['prod_preview']
                    st.rerun()
            elif 'prod_preview' in st.session_state:
                st.warning("No products found matching your criteria.")
        else:
            st.warning(f"DANGER: Delete ALL products on {domain_clean}.")
            confirm = st.text_input(f"Type '{domain_clean}' to confirm:", key="wipe_prod_confirm")
            if st.button("WIPE ALL PRODUCTS", type="primary"):
                if confirm == domain_clean: run_delete_products(del_site, ck, cs, [], auto_threads, True, default_tab_data)
                else: st.error("Confirmation failed.")

    # --- TAB: DELETE MEDIA ---
    with t_media:
        mode_media = st.radio("Option:", ["Visual Selection (Fetch & Select)", "Wipe All Media"], horizontal=True)
        st.divider()

        if "Visual" in mode_media:
            c_filter_m, c_act_m = st.columns([3, 1])
            with c_filter_m:
                fetch_media_ids = st.text_input("Filter by IDs (Optional - comma separated):", placeholder="e.g. 5501, 5502", key="m_ids")
                limit_media = st.slider("Or Fetch Latest (Limit):", 10, 200, 50, step=10, key="lim_m")
            with c_act_m:
                st.write("")
                st.write("")
                if st.button("Fetch Media"):
                    with st.spinner("Fetching Media..."):
                        specific_ids_m = [x.strip() for x in fetch_media_ids.split(',')] if fetch_media_ids.strip() else None
                        data = deleter.get_media_for_ui(del_site['domain_url'], del_site['secret_key'], limit_media, specific_ids_m)
                        st.session_state['media_preview'] = pd.DataFrame(data) if data else pd.DataFrame()

            if 'media_preview' in st.session_state and not st.session_state['media_preview'].empty:
                df_m = st.session_state['media_preview']
                st.caption(f"Found {len(df_m)} items.")

                # [FIXED] Tương tự với tab Media
                c_m_btn1, c_m_btn2, _ = st.columns([2, 2.2, 12], gap="small")
                
                if c_m_btn1.button("Select All", key="sel_all_m"):
                    st.session_state['media_preview']['Select'] = True
                    st.rerun()
                if c_m_btn2.button("Deselect All", key="desel_all_m"):
                    st.session_state['media_preview']['Select'] = False
                    st.rerun()

                edited_df_m = st.data_editor(
                    st.session_state['media_preview'],
                    key="media_editor", 
                    use_container_width=True, 
                    height=450, 
                    hide_index=True,
                    column_config={
                        "Select": st.column_config.CheckboxColumn("Select", default=False),
                        "Thumbnail": st.column_config.ImageColumn("Img", width="small"),
                        "ID": st.column_config.TextColumn("ID", disabled=True),
                    }
                )
                
                selected_media = edited_df_m[edited_df_m["Select"] == True]
                count_media = len(selected_media)
                st.write("")
                if st.button(f"DELETE {count_media} SELECTED IMAGES", type="primary", disabled=(count_media==0)):
                    ids_media = selected_media["ID"].astype(str).tolist()
                    run_delete_media_list(del_site, ids_media, auto_threads)
                    del st.session_state['media_preview']
                    st.rerun()
            elif 'media_preview' in st.session_state: st.warning("No media found.")
        else:
            st.warning("DANGER: Delete ALL images.")
            confirm_media = st.text_input(f"Type '{domain_clean}' to confirm:", key="wipe_media_confirm")
            if st.button("WIPE ALL MEDIA", type="primary"):
                if confirm_media == domain_clean: run_delete_media_all(del_site, auto_threads)
                else: st.error("Confirmation failed.")

# --- EXECUTION HELPERS ---
def run_import(site, tab_name, mode, is_test, threads, filter_ids=None):
    gc = db.init_google_sheets()
    if not gc: return
    sheet_id = site.get('google_sheet_id')
    with st.status("Processing...", expanded=True) as status:
        try:
            sh = gc.open_by_key(sheet_id)
            ws = sh.worksheet(tab_name)
            vals = ws.get_all_values()
            if len(vals) < 2: 
                status.update(label="Sheet is empty!", state="error")
                return
            header = [str(x).strip() for x in vals[0]]
            data = vals[1:]
            df = pd.DataFrame(data, columns=header)
            rows = df.to_dict('records')
            for i, row in enumerate(rows): row['_real_row'] = i + 2
            if filter_ids:
                status.write(f"Filtering {len(filter_ids)} IDs...")
                filtered_rows = []
                id_keys = [k for k in rows[0].keys() if k.lower() in ['id', 'product id', 'sku']]
                if not id_keys:
                    status.update(label="ID Column not found!", state="error")
                    return
                id_key = id_keys[0]
                target_set = {str(x).strip() for x in filter_ids}
                for row in rows:
                    if str(row.get(id_key, '')).strip() in target_set: filtered_rows.append(row)
                rows = filtered_rows
                if not rows:
                    status.update(label="No matching IDs!", state="error")
                    return
            if is_test and not filter_ids: rows = rows[:5]
            status.update(label=f"Processing {len(rows)} items...", state="running")
            pb = st.progress(0)
            logs = importer.process_import(rows, site['domain_url'], site['secret_key'], mode, sheet_id, tab_name, threads, lambda p,c,t: pb.progress(p))
            fail_count = 0
            summary_line = next((l for l in reversed(logs) if "SUMMARY:" in l), None)
            if summary_line:
                try:
                    for p in summary_line.split("|"):
                        if "Failed" in p: fail_count = int(p.strip().split(" ")[-1])
                except: pass
            else: fail_count = sum(1 for l in logs if ("Error" in l or "Failed" in l) and "SUMMARY" not in l)
            if fail_count > 0: 
                st.error(f"Completed with {fail_count} errors.")
                with st.expander("View Logs"): st.write(logs)
            else: 
                st.success("Operation Successful!")
                with st.expander("View Logs"): st.write(logs)
            status.update(label="Finished!", state="complete")
        except Exception as e: st.error(str(e))

def run_check_process(site, tab_name, threads, is_test, is_auto=False):
    gc = db.init_google_sheets()
    if not gc: return
    sheet_id = site.get('google_sheet_id')
    label_start = "Loading data..." if is_auto else "Checking..."
    with st.status(label_start, expanded=True) as status:
        try:
            sh = gc.open_by_key(sheet_id)
            ws = sh.worksheet(tab_name)
            vals = ws.get_all_values()
            if len(vals) < 2: return
            header = [str(x).strip() for x in vals[0]]
            data = vals[1:]
            df = pd.DataFrame(data, columns=header)
            rows = df.to_dict('records')
            if is_test: rows = rows[:5]
            pb = st.progress(0)
            status_text = st.empty()
            logs = checker.process_check_existence(rows, site['domain_url'], site['secret_key'], sheet_id, tab_name, threads, lambda p,c,t: pb.progress(p))
            updated = sum(1 for l in logs if "->" in l)
            if updated > 0: st.success(f"Synced {updated} items.")
            elif not is_auto: st.info("Up to date.")
            status.update(label="Data Load Complete!", state="complete")
        except: status.update(label="Sync Error", state="error")

def run_delete_products(site, ck, cs, ids, threads, wipe, sync_tab):
    secret = site['secret_key']
    deleted_skus = []
    with st.status("Executing Delete...", expanded=True) as s:
        pb = st.progress(0)
        update = lambda p,c,t: pb.progress(p)
        if wipe: logs, deleted_skus = deleter.delete_all_products_scan_mode(site['domain_url'], ck, cs, secret, threads, update)
        else: logs, deleted_skus = deleter.delete_product_list(site['domain_url'], secret, ids, threads, update)
        st.write(logs)
        s.update(label="Delete Completed on Web!", state="complete")
    if sync_tab:
        if wipe: run_check_process(site, sync_tab, threads, False, True)
        else:
            if deleted_skus:
                st.info(f"Syncing {len(deleted_skus)} deleted items back to Sheet...")
                res = deleter.sync_deleted_rows(site['google_sheet_id'], sync_tab, deleted_skus)
                if "Error" in res[0]: st.error(res[0])
                else: st.success(res[0])

def run_delete_media_list(site, ids, threads):
    with st.status("Deleting Media...", expanded=True) as s:
        pb = st.progress(0)
        success_count = 0
        chunks = [ids[i:i + 50] for i in range(0, len(ids), 50)]
        for chunk in chunks:
            if deleter.woo.delete_media_batch(site['domain_url'], site['secret_key'], chunk):
                success_count += len(chunk)
            pb.progress(success_count / len(ids))
        st.success(f"Deleted {success_count} images.")
        s.update(label="Finished!", state="complete")

def run_delete_media_all(site, threads):
    with st.status("Cleaning Media Library...", expanded=True) as s:
        pb = st.progress(0)
        res = deleter.delete_all_media(site['domain_url'], site['secret_key'], threads, lambda p,c,t: pb.progress(p))
        st.write(res)
        s.update(label="Finished!", state="complete")