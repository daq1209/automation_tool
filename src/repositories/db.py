import streamlit as st
import gspread
from supabase import create_client
from google.oauth2 import service_account

# --- SUPABASE CONFIGURATION ---
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
        # Ensure 'service_account.json' is in the root directory
        scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = service_account.Credentials.from_service_account_file('service_account.json', scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets connection error: {e}")
        return None

# --- DATA ACCESS FUNCTIONS ---

def get_all_sites():
    """Fetch sites from Supabase"""
    supabase = init_supabase()
    if not supabase: return []
    try:
        res = supabase.table('woo_sites').select("*").order('id').execute()
        return res.data if res.data else []
    except Exception as e: 
        print(f"DB Error: {e}")
        return []

def check_admin_login(username, password):
    """Check admin credentials"""
    supabase = init_supabase()
    if not supabase: return False
    try:
        res = supabase.table('admin_users').select('*').eq('username', username).eq('password', password).execute()
        return len(res.data) > 0
    except: return False

# --- SHEET UPDATE FUNCTIONS ---

def update_sheet_batch(sheet_id, tab_name, updates):
    """
    Batch update multiple cells at once to avoid API rate limits.
    updates: List of [{'range': 'A2', 'values': [['Done']]}, ...]
    """
    gc = init_google_sheets()
    if not gc or not updates: return

    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        
        # Single request to update all cells
        ws.batch_update(updates)
    except Exception as e:
        print(f"Batch Update Error: {e}")

def update_row_status(sheet_id, tab_name, row_index, status_message):
    """Legacy single row update"""
    gc = init_google_sheets()
    if not gc: return

    try:
        sh = gc.open_by_key(sheet_id)
        ws = sh.worksheet(tab_name)
        ws.update_cell(row_index, 1, str(status_message))
    except Exception as e:
        print(f"Row Update Error: {e}")