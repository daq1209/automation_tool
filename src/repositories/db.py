import streamlit as st
import gspread
import base64
import json
from supabase import create_client
from google.oauth2 import service_account

# --- 1. CONFIGURATION ---
try:
    SUPA_URL = st.secrets["supabase"]["url"]
    SUPA_KEY = st.secrets["supabase"]["key"]
    # [DEBUG] In ra Console xem nó đọc được gì (Chỉ hiện trong Terminal đen, k hiện trên web)
    print(f"DEBUG: Đang kết nối tới URL: {SUPA_URL}")
except Exception as e:
    print(f"DEBUG: Lỗi đọc Secrets: {str(e)}")
    SUPA_URL = ""
    SUPA_KEY = ""

# --- 2. CONNECTION HANDLERS ---

@st.cache_resource
def init_supabase():
    try:
        if not SUPA_URL or not SUPA_KEY:
            print("DEBUG: Thiếu URL hoặc Key!")
            return None
        return create_client(SUPA_URL, SUPA_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")
        return None

@st.cache_resource
def init_google_sheets():
    try:
        if "google" not in st.secrets or "service_account_base64" not in st.secrets["google"]:
            st.error("Missing Google Credentials in secrets.toml")
            return None

        b64_json = st.secrets["google"]["service_account_base64"]
        json_str = base64.b64decode(b64_json).decode("utf-8")
        service_account_info = json.loads(json_str)
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_info(service_account_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets Connection Error: {e}")
        return None

# --- 3. DATA ACCESS FUNCTIONS ---

def get_all_sites():
    supabase = init_supabase()
    if not supabase: return []
    try:
        res = supabase.table('woo_sites').select("*").order('id').execute()
        return res.data if res.data else []
    except Exception as e: 
        print(f"DB Error (get_all_sites): {e}")
        return []

def check_admin_login(username, password):
    """Kiem tra dang nhap Admin"""
    supabase = init_supabase()
    
    # [DEBUG QUAN TRỌNG] Hiển thị lỗi lên màn hình nếu không kết nối được
    if not supabase:
        st.error(f"Lỗi: Không kết nối được Supabase. Kiểm tra secrets.toml. URL hiện tại: {SUPA_URL}")
        return False
        
    try:
        # Thử in ra username đang check
        print(f"DEBUG: Checking user {username}...")
        
        res = supabase.table('admin_users').select('*').eq('username', username).eq('password', password).execute()
        
        # Nếu kết nối được nhưng không tìm thấy user
        if len(res.data) == 0:
            print("DEBUG: Kết nối OK nhưng sai Pass/User")
            return False
            
        return True
    except Exception as e: 
        st.error(f"Lỗi truy vấn DB: {str(e)}")
        return False

# --- 4. SHEET UPDATE FUNCTIONS (GIỮ NGUYÊN) ---
def update_sheet_batch(sheet_id, tab_name, updates):
    gc = init_google_sheets()
    if not gc or not updates: return
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        ws.batch_update(updates)
    except Exception as e:
        print(f"Batch Update Error: {e}")

def update_row_status(sheet_id, tab_name, row_index, status_message):
    gc = init_google_sheets()
    if not gc: return
    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        ws.update_cell(row_index, 1, str(status_message))
    except Exception as e:
        print(f"Row Update Error: {e}")