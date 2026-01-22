import streamlit as st
import pandas as pd
from src.repositories import db, woo
from src.services import importer, deleter, checker, media_updater
from src.utils.common import render_lock_screen, remove_lock_screen

def local_css():
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 3rem; }
        .stButton button { width: 100%; border-radius: 6px; font-weight: 600; }
        .stSelectbox div[data-baseweb="select"] > div { border-radius: 6px; }
        .stTextInput input { border-radius: 6px; }
        [data-testid="stSidebar"] { background-color: #2c3e50; }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] p, [data-testid="stSidebar"] span { color: #ecf0f1; }
        div[data-testid="column"] button { white-space: nowrap !important; width: auto !important; margin: 0px !important; }
        
        /* Tùy chỉnh st.status cho đẹp hơn */
        div[data-testid="stStatusWidget"] {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            background: #f9f9f9;
        }
        </style>
    """, unsafe_allow_html=True)

def render_dashboard():
    local_css()

    with st.sidebar:
        st.title("Admin Console")
        st.write("---")
        st.info("System Ready (V12.3)")
        if st.button("Logout", type="secondary"):
            st.session_state['is_logged_in'] = False
            st.rerun()

    st.title("POD Automation V12.3")
    
    # 1. LOAD CONFIG FIRST
    with st.container(border=True):
        st.markdown("### 1. Global Settings")
        c1, c2, c3 = st.columns(3)
        with c1: default_tab_data = st.text_input("Data Tab Name:", value="Action", key="cfg_tab_data")
        with c2: default_tab_img = st.text_input("Image Tab Name:", value="Action", key="cfg_tab_img")
        with c3: auto_threads = st.slider("Worker Threads (Phase 2):", 1, 30, 20)

    # 2. SELECT SITE
    st.write("")
    st.markdown("### 2. Target Website")
    
    sites = db.get_all_sites()
    if not sites:
        st.error("No websites found in database.")
        return

    site_map = {s['site_name']: s for s in sites}
    site_options = ["-- Select a Website --"] + list(site_map.keys())
    
    if 'previous_site' not in st.session_state: 
        st.session_state['previous_site'] = site_options[0]

    selected_option = st.selectbox("Select Website to Start:", site_options, label_visibility="collapsed")

    if selected_option == site_options[0]:
        st.info("Please select a website to proceed.")
        return

    selected_site = site_map[selected_option]

    # Placeholder for Sync Status (Instant Load)
    sync_status_placeholder = st.empty()

    st.write("") 

    # 3. RENDER MAIN TABS
    tab1, tab2, tab3 = st.tabs(["Import Pipeline (V12)", "Delete Tool", "Images"])

    # === TAB 1: IMPORT ===
    with tab1:
        with st.container(border=True):
            st.markdown("#### Import Scope")
            c_mode, c_info = st.columns([2, 3])
            with c_mode: 
                import_mode = st.radio("Mode:", ["Import All Rows", "Filter by Specific IDs"], horizontal=True)
            
            filter_ids = []
            if import_mode == "Filter by Specific IDs":
                st.info("Enter IDs to match (Start With):")
                txt_filter = st.text_area("Sheet IDs:", height=100, key="import_filter")
                if txt_filter: 
                    filter_ids = [x.strip() for x in txt_filter.replace(',', '\n').split('\n') if x.strip()]
            
            with c_info:
                if filter_ids: st.success(f"Targeting {len(filter_ids)} filter inputs.")
                else: st.info("Target: All rows in Sheet.")

        st.write("")
        st.info("Note: Successful imports -> 'Done' | Published -> '1'")
        
        if st.checkbox("Preview Data (Applied Filter)", value=False):
            render_data_preview(selected_site, default_tab_data, filter_ids)
        
        st.write("")
        if st.button("RUN IMPORT PROCESS", type="primary"):
            # [LOCK UI] Khoa man hinh
            lock = st.empty()
            with lock: render_lock_screen()
            try:
                run_import_v12(selected_site, default_tab_data, auto_threads, filter_ids)
            finally:
                with lock: remove_lock_screen()

    # === TAB 2: DELETE TOOL ===
    with tab2:
        render_delete_tool(sites, list(site_map.keys()), selected_option, default_tab_data, auto_threads)

    # === TAB 3: IMAGES ===
    with tab3:
        st.markdown("#### Sync WordPress Media to Sheet")
        
        c_img1, c_img2 = st.columns(2)
        with c_img1:
            sheet_tab_name = st.text_input("Sheet Tab Name:", value="UpdateImage", key="img_sync_tab")
        with c_img2:
            limit_media = st.number_input("Max Media to Fetch:", min_value=10, max_value=50000, value=5000, step=500)
            
        st.info("Logic: Match by 'ID' or 'Old Slug'. If mismatch -> Error. If 'Slug' matches 'New Slug' -> Done.")
        
        if st.checkbox("Preview Sheet Data", key="img_preview_chk"):
            render_data_preview(selected_site, sheet_tab_name)
        
        st.write("")
        if st.button("RUN MEDIA SYNC", type="primary"):
            lock = st.empty()
            with lock: render_lock_screen()
            try:
                with st.status("Syncing Media...", expanded=True) as status:
                    st.write("1. Fetching media from WordPress...")
                    media_data = media_updater.fetch_all_media(selected_site['domain_url'], selected_site['secret_key'], limit_media)
                    st.write(f"Found {len(media_data)} media items.")
                    
                    st.write("2. Syncing to Google Sheet...")
                    result = media_updater.sync_media_to_sheet(selected_site['google_sheet_id'], sheet_tab_name, media_data)
                    
                    if "error" in result:
                        status.update(label="Sync Failed!", state="error")
                        st.error(result["error"])
                    else:
                        # DEBUG INFO
                        if 'debug_info' in result:
                            with st.expander("Debug Column Info"):
                                st.json(result['debug_info'])
                                
                        msg = f"Updated Sheet: {result['updated']} | Created: {result['created']} | Total Scanned: {result['total']}"
                        
                        # Handle WP Updates
                        if 'wp_updates_queued' in result:
                            queued = result['wp_updates_queued']
                            st.write(f"3. Updating {len(queued)} items on WordPress...")
                            
                            # Show preview of what will change
                            if queued:
                                st.caption("Preview of changes (Title & File Rename):")
                                preview_data = [{
                                    "ID": q['id'], 
                                    "Old Title": q.get('old_title', ''), 
                                    "New Title": q['title'],
                                    "Target Slug": q.get('slug', '(auto)')
                                } for q in queued]
                                st.dataframe(preview_data, height=200)

                            # Chunk updates to avoid timeout
                            res_exe = media_updater.execute_wp_updates(selected_site['domain_url'], selected_site['secret_key'], queued)
                            
                            wp_updated_count = res_exe['updated_count']
                            for log in res_exe['logs']:
                                st.caption(log)
                            
                            msg += f" | WP Titles Updated: {wp_updated_count}"
                        
                        status.update(label="Sync Complete!", state="complete")
                        st.success(msg)
            except Exception as e:
                st.error(f"Critical Error: {e}")
            finally:
                with lock: remove_lock_screen()

    # 4. RUN AUTO SYNC (CHAY NGAM)
    if selected_option != st.session_state['previous_site']:
        st.session_state['previous_site'] = selected_option
        
        # Clear Cache
        if 'prod_preview' in st.session_state: del st.session_state['prod_preview']
        if 'media_preview' in st.session_state: del st.session_state['media_preview']
        
        st.toast(f"Connected to {selected_option}. Syncing...")
        
        # Day noi dung Sync vao Placeholder
        with sync_status_placeholder.container():
            run_sync_initial(selected_site, default_tab_data)


# --- EXECUTION HELPERS ---

def run_sync_initial(site, tab_name):
    # Auto Sync: Khong can canh bao khoa vi chay nhanh
    with st.status(f"Auto-Syncing Sheet with {site['site_name']}...", expanded=True) as status:
        status.write("Fetching SKUs & Scanning Sheet...")
        pb = st.progress(0)
        logs = checker.run_sync_sheet_with_website(site, tab_name, 20, lambda p: pb.progress(p))
        for log in logs:
            st.write(log)
        status.update(label="Sync Completed!", state="complete")

def render_data_preview(site, tab_name, filter_ids=None):
    gc = db.init_google_sheets()
    if not gc: return
    sheet_id = site.get('google_sheet_id')
    with st.spinner("Fetching data..."):
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
                    mask = df[id_key].astype(str).str.strip().apply(lambda x: any(x.startswith(fid) for fid in filter_ids))
                    df = df[mask]
            st.info(f"Total rows: {len(df)}")
            st.dataframe(df, use_container_width=True, hide_index=True, height=400)
        except Exception as e: st.error(f"Error: {e}")

def run_import_v12(site, tab_name, threads, filter_ids=None):
    gc = db.init_google_sheets()
    if not gc: return
    sheet_id = site.get('google_sheet_id')
    
    with st.status("Running Import Pipeline...", expanded=True) as status:
        # [CANH BAO NAM DUOI THANH LOADING]
        st.warning("IMPORTING DATA... PLEASE DO NOT CLOSE THIS TAB")
        
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
                status.write("Applying Filters...")
                id_keys = [k for k in rows[0].keys() if k.lower() in ['id', 'product id', 'sku']]
                if id_keys:
                    id_key = id_keys[0]
                    filtered_rows = [r for r in rows if any(str(r.get(id_key, '')).strip().startswith(fid) for fid in filter_ids)]
                    rows = filtered_rows
                
                if not rows:
                    status.update(label="No items match your filter!", state="error")
                    return

            pb = st.progress(0)
            status.update(label=f"Uploading {len(rows)} items...", state="running")
            
            logs = importer.process_import(rows, site['domain_url'], site['secret_key'], 'data', sheet_id, tab_name, threads, lambda p,c,t: pb.progress(p))
            
            st.write(logs)
            status.update(label="Completed!", state="complete")
            st.success(f"Processed {len(rows)} items.")
        except Exception as e: st.error(str(e))

def render_delete_tool(sites, site_names, selected_name, default_tab_data, auto_threads):
    del_site = next((s for s in sites if s['site_name'] == selected_name), None)
    if not del_site: return
    
    ck = del_site.get('consumer_key') or ""
    cs = del_site.get('consumer_secret') or ""
    secret = del_site.get('secret_key') or ""
    
    t_prod, t_media = st.tabs(["Delete Products", "Delete Media"])
    with t_prod:
        mode = st.radio("Mode:", ["Visual Selection", "Wipe All"], horizontal=True)
        st.divider()
        if mode == "Visual Selection":
            c1, c2 = st.columns([3, 1])
            with c1: search = st.text_input("Search ID/SKU:")
            with c2: limit = st.number_input("Limit:", 10, 200, 50)
            if st.button("Fetch"):
                s_inp = search if search else None
                data = deleter.get_products_for_ui(del_site['domain_url'], secret, limit, s_inp)
                st.session_state['prod_preview'] = pd.DataFrame(data) if data else pd.DataFrame()
            
            if 'prod_preview' in st.session_state and not st.session_state['prod_preview'].empty:
                edited = st.data_editor(st.session_state['prod_preview'], key="pe", use_container_width=True)
                sel = edited[edited["Select"]==True]
                if st.button(f"Delete {len(sel)} items"):
                    # [LOCK UI]
                    lock = st.empty()
                    with lock: render_lock_screen()
                    try:
                        with st.status("Deleting...", expanded=True):
                            st.warning("DELETING DATA... DO NOT CLOSE THIS TAB")
                            logs, d_skus = deleter.delete_product_list(del_site['domain_url'], secret, sel['ID'].astype(str).tolist(), auto_threads)
                            deleter.sync_deleted_rows(del_site['google_sheet_id'], default_tab_data, d_skus)
                            st.success("Deleted & Synced.")
                            del st.session_state['prod_preview']
                            st.rerun()
                    finally:
                        with lock: remove_lock_screen()
        else:
             st.warning("DANGER: This will delete ALL products on the website.")
             if st.button("CONFIRM WIPE ALL PRODUCTS", type="primary"):
                 # [LOCK UI]
                 lock = st.empty()
                 with lock: render_lock_screen()
                 try:
                     with st.status("Wiping All Products...", expanded=True):
                         st.warning("WIPING DATA... DO NOT CLOSE THIS TAB")
                         logs, d_skus = deleter.delete_all_products_scan_mode(del_site['domain_url'], ck, cs, secret, auto_threads)
                         deleter.sync_deleted_rows(del_site['google_sheet_id'], default_tab_data, d_skus)
                         st.success("Wipe command sent and synced.")
                 finally:
                     with lock: remove_lock_screen()

    with t_media:
        mode_m = st.radio("Mode:", ["Visual Media", "Wipe All Media"], horizontal=True)
        st.divider()
        if mode_m == "Visual Media":
            if st.button("Fetch Media"):
                 data = deleter.get_media_for_ui(del_site['domain_url'], secret, 50, None)
                 st.session_state['media_preview'] = pd.DataFrame(data) if data else pd.DataFrame()
            if 'media_preview' in st.session_state and not st.session_state['media_preview'].empty:
                edited_m = st.data_editor(st.session_state['media_preview'], key="me", use_container_width=True)
                sel_m = edited_m[edited_m["Select"]==True]
                if st.button(f"Delete {len(sel_m)} images"):
                    lock = st.empty()
                    with lock: render_lock_screen()
                    try:
                        with st.status("Deleting Media..."):
                            st.warning("PROCESSING... DO NOT CLOSE")
                            deleter.woo.delete_media_batch(del_site['domain_url'], secret, sel_m['ID'].astype(str).tolist())
                            st.success("Deleted.")
                            del st.session_state['media_preview']
                            st.rerun()
                    finally:
                        with lock: remove_lock_screen()
        else:
            if st.button("CONFIRM WIPE ALL MEDIA", type="primary"):
                lock = st.empty()
                with lock: render_lock_screen()
                try:
                    with st.status("Wiping Media..."):
                        st.warning("PROCESSING... DO NOT CLOSE")
                        deleter.delete_all_media(del_site['domain_url'], secret, auto_threads)
                        st.success("Media wipe started.")
                finally:
                    with lock: remove_lock_screen()