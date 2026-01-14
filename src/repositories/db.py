import streamlit as st
import gspread
from supabase import create_client
from google.oauth2 import service_account

# Cấu hình Supabase
try:
    SUPA_URL = "https://ulmtzfgxjidsopxtapwf.supabase.co"
    SUPA_KEY = "sb_publishable_8_xCv3TMJiyHtM_Ug_gAgQ_IrBf5Vdq"
except:
    pass

@st.cache_resource
def init_supabase():
    try:
        return create_client(SUPA_URL, SUPA_KEY)
    except:
        return None

@st.cache_resource
def init_google_sheets():
    try:
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_file('service_account.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets connection error: {e}")
        return None

def get_all_sites():
    """Lấy danh sách site từ Supabase"""
    supabase = init_supabase()
    if not supabase: return []
    try:
        return supabase.table('woo_sites').select("*").order('id').execute().data
    except: return []

def check_admin_login(username, password):
    """Kiểm tra đăng nhập"""
    supabase = init_supabase()
    if not supabase: return False
    try:
        res = supabase.table('admin_users').select('*').eq('username', username).eq('password', password).execute()
        return len(res.data) > 0
    except: return False

# --- HÀM MỚI THÊM CHO GIAI ĐOẠN 1 ---
def update_row_status(sheet_id, tab_name, row_index, status_message):
    """
    Ghi trạng thái vào Cột 1 (Cột A) của dòng tương ứng.
    row_index: Số thứ tự dòng (Header là 1, Dữ liệu bắt đầu từ 2).
    """
    gc = init_google_sheets()
    if not gc: return

    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        # update_cell(row, col, value)
        ws.update_cell(row_index, 1, str(status_message))
    except Exception as e:
        print(f"Lỗi ghi Sheet dòng {row_index}: {e}")