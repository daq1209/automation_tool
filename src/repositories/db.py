import streamlit as st
import gspread
import base64
import json
from supabase import create_client, Client
import pandas as pd
from google.oauth2 import service_account
import bcrypt
from src.utils.logger import logger

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
            st.error("DEBUG INFO: Không tìm thấy URL hoặc Key trong Secrets!")
            return None
        return create_client(SUPA_URL, SUPA_KEY)
    except Exception as e:
        st.error(f"DEBUG INFO: Lỗi khởi tạo Supabase: {str(e)}")
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
    except AttributeError as e:
        logger.error(f"Supabase table access error in get_all_sites: {e}")
        return []
    except Exception as e:
        logger.error(f"Database error in get_all_sites: {e}", exc_info=True)
        return []

def check_admin_login(username, password):
    """
    Kiểm tra mật khẩu admin từ Supabase với bcrypt hashing.
    
    Hỗ trợ cả password_hash (bcrypt) và password (plaintext) để migration từ từ.
    
    Args:
        username: Tên đăng nhập
        password: Mật khẩu plaintext từ form
        
    Returns:
        bool: True nếu đăng nhập thành công
    """
    supabase = init_supabase()
    try:
        logger.info(f"Login attempt for user: {username}")
        
        # Lấy thông tin user
        res = supabase.table('admin_users').select('username, password, password_hash').eq('username', username).execute()
        
        if len(res.data) == 0:
            logger.warning(f"User not found: {username}")
            return False
        
        user_data = res.data[0]
        
        # Ưu tiên dùng password_hash (bcrypt) nếu có
        if user_data.get('password_hash'):
            try:
                is_valid = bcrypt.checkpw(
                    password.encode('utf-8'),
                    user_data['password_hash'].encode('utf-8')
                )
                if is_valid:
                    logger.info(f"Login successful (hashed): {username}")
                else:
                    logger.warning(f"Login failed (invalid password): {username}")
                return is_valid
            except Exception as e:
                logger.error(f"Bcrypt error for {username}: {str(e)}")
                return False
        
        # Fallback: Dùng plaintext password (cho migration)
        # DEPRECATED - Nên migrate sang password_hash
        elif user_data.get('password'):
            is_valid = user_data['password'] == password
            if is_valid:
                logger.warning(f"Login successful (plaintext - DEPRECATED): {username}")
            else:
                logger.warning(f"Login failed (plaintext): {username}")
            return is_valid
        
        logger.error(f"No password method available for user: {username}")
        return False
        
    except Exception as e: 
        logger.error(f"Database error during login: {str(e)}")
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