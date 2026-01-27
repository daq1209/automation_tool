import streamlit as st
import pandas as pd
from src.repositories import db, woo
from src.services import importer, deleter, checker, media_updater
from src.utils.common import render_lock_screen, remove_lock_screen
from src.utils.email_service import email_service
from src.utils.locales import get_text
from src.ui import updater_ui


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

    # --- LANGUAGE STATE ---
    if 'lang' not in st.session_state:
        st.session_state['lang'] = 'vi' # Default to Vietnamese
    
    lang = st.session_state['lang']
    
    with st.sidebar:
        st.title(get_text("nav_title", lang))
        st.write("---")
        
        # LANGUAGE SELECTOR
        lang_code = st.radio("Language / Ngôn ngữ", ["Tiếng Việt", "English"], index=0 if lang == 'vi' else 1)
        st.session_state['lang'] = 'vi' if lang_code == "Tiếng Việt" else 'en'
        lang = st.session_state['lang'] # Update local var
        
        st.write("---")

        # SIDEBAR NAVIGATION
        nav_options = [
            get_text("nav_dashboard", lang),
            get_text("nav_updater", lang),
            get_text("nav_user_mgmt", lang)
        ]
        # Map back to internal keys for logic
        nav_map = {
            get_text("nav_dashboard", lang): "Dashboard",
            get_text("nav_updater", lang): "Data Updater",
            get_text("nav_user_mgmt", lang): "User Management"
        }
        
        nav_selection = st.radio(get_text("nav_menu_label", lang), nav_options, index=0)
        nav_mode = nav_map[nav_selection]

        # Logout Logic (moved down)
        st.write("---")
        st.caption("Environment: Production")
        if st.button(get_text("logout_btn", lang), type="secondary"):
            st.session_state['is_logged_in'] = False
            st.rerun()
        
        st.write("---")
        
        # GLOBAL SETTINGS (MOVED TO SIDEBAR)
        with st.expander(get_text("settings_label", lang), expanded=False):
            auto_threads = st.slider(get_text("threads_label", lang), 1, 30, 20)

    st.title("POD Automation Environment")
    
    # 0. EARLY ROUTING (No Site Selection Needed)
    if nav_mode == "User Management":
        render_user_management_screen()
        return

    # 1. SELECT SITE
    st.write("")
    st.markdown(f"### {get_text('site_select_header', lang)}")
    
    sites = db.get_all_sites()
    if not sites:
        st.error("No websites found in database.")
        return

    site_map = {s['site_name']: s for s in sites}
    site_options = [get_text("site_select_default", lang)] + list(site_map.keys())
    
    if 'previous_site' not in st.session_state: 
        st.session_state['previous_site'] = site_options[0]

    selected_option = st.selectbox(get_text("site_select_label", lang), site_options, label_visibility="collapsed")

    if selected_option == site_options[0]:
        st.info(get_text("site_select_prompt", lang))
        return


    selected_site = site_map[selected_option]

    # Placeholder for Sync Status (Instant Load)
    sync_status_placeholder = st.empty()

    st.write("") 
    
    # ROUTER
    if nav_mode == "Data Updater":
        updater_ui.render_updater_ui(selected_site)
        return

    # FETCH TABS ONCE
    sheet_tabs = db.get_worksheet_titles(selected_site['google_sheet_id'])
    if not sheet_tabs:
        sheet_tabs = ["Sheet1"] # Fallback

    # 3. RENDER MAIN TABS
    tab1, tab2, tab3 = st.tabs([
        get_text("tab_import", lang), 
        get_text("tab_delete", lang), 
        get_text("tab_images", lang)
    ])

    # === TAB 1: IMPORT ===
    with tab1:
        with st.expander(get_text("guide_import_title", lang)):
            st.markdown(get_text("guide_import_content", lang))
        with st.container(border=True):
            st.markdown(f"#### {get_text('config_header', lang)}")
            c_conf1, c_conf2 = st.columns(2)
            with c_conf1:
                default_tab_data = st.selectbox(get_text("tab_data_label", lang), sheet_tabs, index=0 if "Action" not in sheet_tabs else sheet_tabs.index("Action"), key="cfg_tab_data")
            with c_conf2:
                default_tab_img = st.selectbox(get_text("tab_img_label", lang), sheet_tabs, index=0 if "Action" not in sheet_tabs else sheet_tabs.index("Action"), key="cfg_tab_img")


        with st.container(border=True):
            st.markdown(f"#### {get_text('import_scope_header', lang)}")
            c_mode, c_info = st.columns([2, 3])
            with c_mode: 
                import_mode = st.radio(get_text("mode_label", lang), [get_text("mode_all", lang), get_text("mode_filter", lang)], horizontal=True)
            
            filter_ids = []
            if import_mode == get_text("mode_filter", lang):
                st.info(f"{get_text('filter_input_label', lang)} (Start With)")
                txt_filter = st.text_area("IDs:", height=100, key="import_filter")
                if txt_filter: 
                    filter_ids = [x.strip() for x in txt_filter.replace(',', '\n').split('\n') if x.strip()]
            
            with c_info:
                if filter_ids: st.success(f"Targeting {len(filter_ids)} filter inputs.")
                else: st.info("Target: All rows in Sheet.")

        st.write("")
        st.info(get_text("import_note", lang))
        
        c_preview, c_refresh = st.columns([2, 1])
        with c_preview:
            show_preview = st.checkbox(get_text("preview_chk", lang), value=False)
        with c_refresh:
            if show_preview and st.button(get_text("refresh_btn", lang), key="refresh_import"):
                st.rerun()

        if show_preview:
            render_data_preview(selected_site, default_tab_data, filter_ids)
        
        st.write("")
        if st.button(get_text("run_import_btn", lang), type="primary"):
            # [LOCK UI] Khoa man hinh
            lock = st.empty()
            with lock: render_lock_screen()
            try:
                run_import_v12(selected_site, default_tab_data, auto_threads, filter_ids)
            finally:
                with lock: remove_lock_screen()

    # === TAB 2: DELETE TOOL ===
    with tab2:
        render_delete_tool(sites, list(site_map.keys()), selected_option, default_tab_data, auto_threads, lang)


    # === TAB 3: IMAGES ===
    with tab3:
        with st.expander(get_text("guide_img_title", lang)):
            st.markdown(get_text("guide_img_content", lang))
        st.markdown(f"#### {get_text('sync_header', lang)}")
        
        c_img1, c_img2 = st.columns(2)
        with c_img1:
            sheet_tab_name = st.selectbox(get_text("tab_img_label", lang), sheet_tabs, index=0 if "UpdateImage" not in sheet_tabs else sheet_tabs.index("UpdateImage"), key="img_sync_tab")
        with c_img2:
            limit_media = st.selectbox(get_text("limit_label", lang), [5000, 10000, 25000, 50000, 100000, 200000], index=0)
            
        st.info("Logic: Match by 'ID' or 'Old Slug'. If mismatch -> Error. If 'Slug' matches 'New Slug' -> Done.")
        
        c_img_prev, c_img_ref = st.columns([2, 1])
        with c_img_prev:
            show_img_preview = st.checkbox(get_text("preview_sheet_chk", lang), key="img_preview_chk")
        with c_img_ref:
            if show_img_preview and st.button(get_text("refresh_btn", lang), key="refresh_images"):
                st.rerun()

        if show_img_preview:
            render_data_preview(selected_site, sheet_tab_name)
        
        st.write("")
        if st.button(get_text("run_sync_btn", lang), type="primary"):
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

    # (Tab 4 User Management moved to Sidebar)

    # (Tab 4 User Management moved to Sidebar)

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

def render_delete_tool(sites, site_names, selected_name, default_tab_data, auto_threads, lang):
    del_site = next((s for s in sites if s['site_name'] == selected_name), None)
    if not del_site: return
    
    ck = del_site.get('consumer_key') or ""
    cs = del_site.get('consumer_secret') or ""
    secret = del_site.get('secret_key') or ""
    
    t_prod, t_media = st.tabs([get_text("tab_del_prod", lang), get_text("tab_del_media", lang)])
    with t_prod:
        with st.expander(get_text("guide_delete_title", lang)):
             st.markdown(get_text("guide_delete_content", lang))
        mode = st.radio(get_text("mode_label", lang), [get_text("mode_visual", lang), get_text("mode_wipe", lang)], horizontal=True)
        st.divider()
        if mode == get_text("mode_visual", lang):
            c1, c2 = st.columns([3, 1])
            with c1: search = st.text_input(get_text("search_label", lang))
            with c2: limit = st.number_input(get_text("limit_label", lang), 10, 200, 50)
            if st.button(get_text("fetch_btn", lang)):
                s_inp = search if search else None
                data = deleter.get_products_for_ui(del_site['domain_url'], secret, limit, s_inp)
                st.session_state['prod_preview'] = pd.DataFrame(data) if data else pd.DataFrame()
            
            if 'prod_preview' in st.session_state and not st.session_state['prod_preview'].empty:
                edited = st.data_editor(st.session_state['prod_preview'], key="pe", use_container_width=True)
                sel = edited[edited["Select"]==True]
                if st.button(get_text("delete_sel_btn", lang).format(len(sel))):
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
             st.warning(get_text("danger_warn", lang))
             if st.button(get_text("confirm_wipe_btn", lang), type="primary"):
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

def render_user_management_screen():
    st.markdown("#### User Management")
    
    # Get current admin info
    current_username = st.session_state.get('username')
    current_admin = db.get_admin_info(current_username)
    
    if not current_admin:
        st.error("Error loading admin profile. Please login again.")
    else:
        # PENDING APPROVALS
        st.subheader("Pending Approvals")
        
        pending_users = db.get_pending_users()
        
        if not pending_users:
            st.info("No pending approvals.")
        else:
            for user in pending_users:
                with st.expander(f"{user['username']} ({user['email']})", expanded=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    with c1:
                        st.write(f"**Registered:** {user['created_at']}")
                        st.write(f"**Email:** {user['email']}")
                    with c2:
                        if st.button("Approve", key=f"app_{user['id']}", use_container_width=True):
                            success, msg, user_info = db.approve_user(user['id'], current_admin['id'])
                            if success:
                                st.success(f"Approved {user['username']}")
                                email_service.send_approval_notification(user['email'], user['username'])
                                st.rerun()
                            else:
                                st.error(msg)
                    with c3:
                        if st.button("Reject", key=f"rej_{user['id']}", type="primary", use_container_width=True):
                            success, msg = db.reject_user(user['id'])
                            if success:
                                st.warning(f"Rejected {user['username']}")
                                st.rerun()
                            else:
                                st.error(msg)
        
        st.divider()
        
        # ADMIN LIST (READ ONLY)
        st.subheader("Active Admins")
        admins = db.get_all_admins()
        if admins:
            st.write(f"Total Active Admins: {len(admins)}")
            with st.expander("View Admin Emails"):
                for email in admins:
                    st.text(f"• {email}")