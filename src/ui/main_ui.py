import streamlit as st
import pandas as pd
from datetime import date
from src.repositories import db
from src.services import importer, deleter

def render_dashboard():
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("Admin Panel")
        if st.button("Logout"):
            st.session_state['is_logged_in'] = False
            st.rerun()

    st.markdown("## POD Automation Environment")
    
    sites = db.get_all_sites()
    if not sites:
        st.warning("No sites found in Supabase.")
        return

    tab1, tab2 = st.tabs(["Import Tool", "Delete Tool"])

    # ==========================
    # TAB 1: IMPORT TOOL
    # ==========================
    with tab1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Configuration")
        
        site_names = [s['site_name'] for s in sites]
        selected_name = st.selectbox("Select Website:", site_names)
        selected_site = next((s for s in sites if s['site_name'] == selected_name), None)

        col1, col2 = st.columns(2)
        with col1: tab_data = st.text_input("Tab Data:", value="Action")
        with col2: tab_img = st.text_input("Tab Image:", value="Action")

        col3, col4 = st.columns(2)
        with col3: is_test = st.checkbox("Test Mode (5 rows)", value=True)
        with col4: threads = st.slider("Threads (Import)", 1, 10, 4)
        
        st.markdown('</div>', unsafe_allow_html=True)

        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.info(f"Step 1: Import Text ({tab_data})")
            if st.button("RUN STEP 1: IMPORT DATA", type="primary"):
                run_import(selected_site, tab_data, 'data', is_test, threads)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_act2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.info(f"Step 2: Sync Images ({tab_img})")
            if st.button("RUN STEP 2: SYNC IMAGES", type="secondary"):
                run_import(selected_site, tab_img, 'image', is_test, threads)
            st.markdown('</div>', unsafe_allow_html=True)

    # ==========================
    # TAB 2: DELETE TOOL
    # ==========================
    with tab2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Delete Configuration")
        
        del_name = st.selectbox("Select Website:", site_names, key="del_s")
        del_site = next((s for s in sites if s['site_name'] == del_name), None)
        
        db_ck = del_site.get('consumer_key') or ""
        db_cs = del_site.get('consumer_secret') or ""
        
        c1, c2 = st.columns(2)
        ck = c1.text_input("Consumer Key", value=db_ck, type="password")
        cs = c2.text_input("Consumer Secret", value=db_cs, type="password")
        
        # Lấy domain sạch để dùng cho việc Confirm (bỏ https://)
        domain_confirm = del_site['domain_url'].replace('https://', '').replace('http://', '').strip('/')
        
        st.markdown('</div>', unsafe_allow_html=True)

        if del_site:
            t_prod, t_media = st.tabs(["Delete Products", "Delete Media"])

            # --- SUB-TAB: PRODUCTS ---
            with t_prod:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                mode_prod = st.radio("Action:", ["Delete List", "Wipe All"], horizontal=True)
                p_threads = st.slider("Threads:", 1, 20, 10, key="pt")
                st.markdown("---")

                if mode_prod == "Delete List":
                    txt_ids = st.text_area("Product IDs:")
                    if st.button("DELETE LIST"):
                        ids = [x.strip() for x in txt_ids.replace(',', '\n').split('\n') if x.strip()]
                        if ids:
                            run_delete_products(del_site, ck, cs, ids, p_threads, is_wipe=False)
                
                else: # Wipe All
                    st.error("⚠️ DANGER ZONE: Deleting ALL products.")
                    st.write(f"To confirm, please type **{domain_confirm}** in the box below:")
                    
                    user_confirm = st.text_input("Confirmation:", placeholder=domain_confirm, key="cf_prod")
                    
                    if st.button("🔥 WIPE ALL PRODUCTS", type="secondary"):
                        if user_confirm == domain_confirm:
                            run_delete_products(del_site, ck, cs, [], p_threads, is_wipe=True)
                        else:
                            st.error("Incorrect confirmation text. Action aborted.")
                            
                st.markdown('</div>', unsafe_allow_html=True)

            # --- SUB-TAB: MEDIA ---
            with t_media:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                mode_media = st.radio("Action:", ["Wipe All Media", "Delete by Date"], horizontal=True)
                st.markdown("---")

                if mode_media == "Wipe All Media":
                    m_threads = st.slider("Threads:", 1, 50, 20, key="mt")
                    st.warning("⚠️ This will delete ALL images.")
                    st.write(f"To confirm, please type **{domain_confirm}** below:")
                    
                    user_confirm_media = st.text_input("Confirmation:", placeholder=domain_confirm, key="cf_media")
                    
                    if st.button("🔥 WIPE IMAGES", type="primary"):
                        if user_confirm_media == domain_confirm:
                             run_delete_media_all(del_site, m_threads)
                        else:
                            st.error("Incorrect confirmation text.")

                else: # Date
                    d1 = st.date_input("Start", date.today())
                    d2 = st.date_input("End", date.today())
                    if st.button("DELETE BY DATE"):
                        with st.status("Deleting..."):
                            from src.repositories import woo
                            res = woo.delete_media_by_date_range(del_site['domain_url'], del_site['secret_key'], d1, d2)
                            if res and res.status_code == 200: st.success("Success!")
                            else: st.error("Failed")
                st.markdown('</div>', unsafe_allow_html=True)

# --- HELPER: IMPORT ---
def run_import(site, tab_name, mode, is_test, threads):
    # (Hàm này giữ nguyên như Giai đoạn 1)
    gc = db.init_google_sheets()
    if not gc: return
    sheet_id = site.get('google_sheet_id')
    if not sheet_id: return
    with st.status("Preparing Data...", expanded=True) as status:
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
            status.update(label=f"Importing {len(rows)} items...", state="running")
            pb = st.progress(0)
            logs = importer.process_import(
                data_rows=rows, domain=site['domain_url'], secret=site['secret_key'], 
                mode=mode, sheet_id=sheet_id, tab_name=tab_name, max_workers=threads,
                progress_callback=lambda p, c, t: pb.progress(p)
            )
            for log in logs:
                if "Failed" in log: st.error(log)
                elif "SUMMARY" in log: st.success(log)
            status.update(label="Completed!", state="complete")
        except Exception as e: st.error(f"Error: {str(e)}")

# --- HELPER: DELETE PRODUCTS (New Logic with Progress) ---
def run_delete_products(site, ck, cs, ids, threads, is_wipe):
    with st.status("Processing...", expanded=True) as status:
        pb = st.progress(0)
        status_text = st.empty()
        
        def update_ui(pct, current, total):
            pb.progress(pct)
            status_text.text(f"Deleted: {current}/{total} items")
            
        if is_wipe:
            status.update(label="Scanning & Wiping Store...", state="running")
            logs = deleter.delete_all_products_scan_mode(
                site['domain_url'], ck, cs, max_workers=threads,
                progress_callback=update_ui
            )
        else:
            status.update(label=f"Deleting {len(ids)} items...", state="running")
            logs = deleter.delete_product_list(
                site['domain_url'], ck, cs, ids, max_workers=threads,
                progress_callback=update_ui
            )
            
        st.write(logs)
        status.update(label="Completed!", state="complete")

# --- HELPER: DELETE MEDIA ALL (New Logic with Progress) ---
def run_delete_media_all(site, threads):
    with st.status("Wiping Media...", expanded=True) as status:
        pb = st.progress(0)
        status_text = st.empty()

        def update_ui(pct, current, total):
            pb.progress(pct)
            status_text.text(f"Deleted: {current}/{total} images")

        is_ok, msg = deleter.delete_all_media(
            site['domain_url'], site['secret_key'], max_workers=threads,
            progress_callback=update_ui
        )
        
        if is_ok: st.success(msg)
        else: st.error(msg)
        status.update(label="Completed!", state="complete")