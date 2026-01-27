import streamlit as st
import gspread
import base64
import json
from supabase import create_client, Client
import pandas as pd
from google.oauth2 import service_account
import bcrypt
import secrets
from datetime import datetime, timedelta
from typing import Tuple, Optional, List, Dict
from src.utils.logger import logger
from config import Config

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

def get_worksheet_titles(sheet_id):
    """Fetch all worksheet titles from a Google Sheet."""
    client = init_google_sheets()
    if not client: return []
    try:
        sh = client.open_by_key(sheet_id)
        return [ws.title for ws in sh.worksheets()]
    except Exception as e:
        logger.error(f"Error fetching worksheets for {sheet_id}: {e}")
        st.error(f"Could not load Sheet Tabs: {e}")
        return []

def check_admin_login(username: str, password: str) -> bool:
    """
    Enhanced login with account status checks and auto-migration.
    
    Checks:
    - User exists
    - Account is verified (is_verified = true)
    - Account is approved (is_approved = true) 
    - Account is active (is_active = true)
    - Account is not locked
    - Password is correct
    - Auto-upgrade plaintext → bcrypt
    
    Args:
        username: Username
        password: Password plaintext from form
        
    Returns:
        bool: True if login successful
    """
    supabase = init_supabase()
    if not supabase:
        return False
    
    try:
        logger.info(f"Login attempt for user: {username}")
        
        # Get user with all status fields
        res = supabase.table('admin_users').select(
            'id, username, password, password_hash, is_verified, is_approved, is_active, '
            'failed_login_attempts, locked_until'
        ).eq('username', username).execute()
        
        if len(res.data) == 0:
            logger.warning(f"User not found: {username}")
            return False
        
        user = res.data[0]
        user_id = user['id']
        
        # Check account locked
        if user.get('locked_until'):
            locked_until = datetime.fromisoformat(user['locked_until'].replace('Z', '+00:00'))
            if datetime.now(locked_until.tzinfo) < locked_until:
                logger.warning(f"Account locked: {username} until {locked_until}")
                st.error(f"Account locked until {locked_until.strftime('%Y-%m-%d %H:%M:%S')}")
                return False
            else:
                # Auto-unlock if time passed
                supabase.table('admin_users').update({
                    'locked_until': None,
                    'is_active': True
                }).eq('id', user_id).execute()
                logger.info(f"Auto-unlocked account: {username}")
        
        # Check account status
        if not user.get('is_verified', False):
            logger.warning(f"Account not verified: {username}")
            st.error("Please verify your email address first.")
            return False
        
        if not user.get('is_approved', False):
            logger.warning(f"Account not approved: {username}")
            st.error("Your account is pending admin approval.")
            return False
        
        if not user.get('is_active', True):
            logger.warning(f"Account inactive: {username}")
            st.error("Your account has been deactivated. Contact admin.")
            return False
        
        # Verify password
        is_valid = False
        
        # Try bcrypt first (preferred)
        if user.get('password_hash'):
            try:
                is_valid = bcrypt.checkpw(
                    password.encode('utf-8'),
                    user['password_hash'].encode('utf-8')
                )
            except Exception as e:
                logger.error(f"Bcrypt error for {username}: {e}")
                increment_failed_login(username)
                return False
        
        # Fallback: plaintext (GRACE PERIOD - Auto-upgrade)
        elif user.get('password'):
            if user['password'] == password:
                is_valid = True
                # AUTO-UPGRADE: Hash password immediately
                try:
                    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    supabase.table('admin_users').update({
                        'password_hash': new_hash,
                        'password': None  # Remove plaintext
                    }).eq('id', user_id).execute()
                    logger.info(f"Auto-migrated {username} to bcrypt")
                except Exception as e:
                    logger.error(f"Failed to auto-migrate {username}: {e}")
        
        # Handle login result
        if is_valid:
            # Reset failed attempts on successful login
            supabase.table('admin_users').update({
                'failed_login_attempts': 0
            }).eq('id', user_id).execute()
            logger.info(f"Login successful: {username}")
            return True
        else:
            # Increment failed attempts
            increment_failed_login(username)
            logger.warning(f"Login failed (invalid password): {username}")
            return False
            
    except Exception as e:
        logger.error(f"Database error during login: {e}", exc_info=True)
        st.error(f"Login error: {str(e)}")
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


# --- 5. USER MANAGEMENT FUNCTIONS ---

def create_user(username: str, email: str, password: str) -> Tuple[bool, str]:
    """
    Create new user with email verification required.
    
    Args:
        username: Unique username
        email: Unique email address
        password: Password (will be hashed)
        
    Returns:
        Tuple of (success: bool, message_or_token: str)
    """
    supabase = init_supabase()
    if not supabase:
        return False, "Database connection error"
    
    try:
        # Check username exists
        res = supabase.table('admin_users').select('id').eq('username', username).execute()
        if res.data:
            return False, "Username already exists"
        
        # Check email exists
        res = supabase.table('admin_users').select('id').eq('email', email).execute()
        if res.data:
            return False, "Email already registered"
        
        # Generate verification token
        verification_token = secrets.token_urlsafe(32)
        token_expires = datetime.now() + timedelta(seconds=Config.VERIFICATION_TOKEN_EXPIRY)
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        new_user = {
            'username': username.lower(),
            'email': email.lower(),
            'password_hash': password_hash,
            'is_verified': False,
            'is_approved': False,
            'is_active': False,
            'verification_token': verification_token,
            'verification_token_expires': token_expires.isoformat(),
            'created_at': datetime.now().isoformat()
        }
        
        supabase.table('admin_users').insert(new_user).execute()
        logger.info(f"User created: {username} ({email})")
        return True, verification_token
        
    except Exception as e:
        logger.error(f"Error creating user {username}: {e}", exc_info=True)
        return False, f"Error: {str(e)}"


def verify_email(token: str) -> Tuple[bool, str]:
    """
    Verify user email with token.
    
    Args:
        token: Verification token from email
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    supabase = init_supabase()
    if not supabase:
        return False, "Database connection error"
    
    try:
        # Find user with token
        res = supabase.table('admin_users').select(
            'id, username, email, verification_token_expires'
        ).eq('verification_token', token).execute()
        
        if not res.data:
            return False, "Invalid verification token"
        
        user = res.data[0]
        
        # Check token expiry
        expires = datetime.fromisoformat(user['verification_token_expires'].replace('Z', '+00:00'))
        if datetime.now(expires.tzinfo) > expires:
            return False, "Verification link expired. Please register again."
        
        # Update user as verified
        supabase.table('admin_users').update({
            'is_verified': True,
            'verification_token': None,
            'verification_token_expires': None
        }).eq('id', user['id']).execute()
        
        logger.info(f"Email verified: {user['username']}")
        return True, f"Email verified successfully for {user['username']}"
        
    except Exception as e:
        logger.error(f"Error verifying email: {e}", exc_info=True)
        return False, f"Verification error: {str(e)}"


def request_password_reset(email: str) -> Tuple[bool, str, Optional[str]]:
    """
    Generate password reset token.
    
    Args:
        email: User's email address
        
    Returns:
        Tuple of (success: bool, message: str, token: Optional[str])
    """
    supabase = init_supabase()
    if not supabase:
        return False, "Database connection error", None
    
    try:
        # Find user by email
        res = supabase.table('admin_users').select('id, username, email').eq('email', email.lower()).execute()
        
        if not res.data:
            # Don't reveal if email exists (prevent enumeration)
            return True, "If email exists, reset link sent", None
        
        user = res.data[0]
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        token_expires = datetime.now() + timedelta(seconds=Config.RESET_TOKEN_EXPIRY)
        
        # Update user
        supabase.table('admin_users').update({
            'reset_token': reset_token,
            'reset_token_expires': token_expires.isoformat()
        }).eq('id', user['id']).execute()
        
        logger.info(f"Password reset requested: {user['username']}")
        return True, "Reset link sent", reset_token
        
    except Exception as e:
        logger.error(f"Error requesting password reset: {e}", exc_info=True)
        return False, f"Error: {str(e)}", None


def reset_password(token: str, new_password: str) -> Tuple[bool, str]:
    """
    Reset password with valid token.
    
    Args:
        token: Reset token from email
        new_password: New password (plaintext, will be hashed)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    supabase = init_supabase()
    if not supabase:
        return False, "Database connection error"
    
    try:
        # Find user with token
        res = supabase.table('admin_users').select(
            'id, username, reset_token_expires'
        ).eq('reset_token', token).execute()
        
        if not res.data:
            return False, "Invalid or expired reset token"
        
        user = res.data[0]
        
        # Check token expiry
        expires = datetime.fromisoformat(user['reset_token_expires'].replace('Z', '+00:00'))
        if datetime.now(expires.tzinfo) > expires:
            return False, "Reset link expired. Please request a new one."
        
        # Hash new password
        password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Update password and clear reset token
        supabase.table('admin_users').update({
            'password_hash': password_hash,
            'password': None,  # Remove plaintext if any
            'reset_token': None,
            'reset_token_expires': None,
            'failed_login_attempts': 0,  # Reset failed attempts
            'locked_until': None  # Unlock account
        }).eq('id', user['id']).execute()
        
        logger.info(f"Password reset successful: {user['username']}")
        return True, "Password reset successful"
        
    except Exception as e:
        logger.error(f"Error resetting password: {e}", exc_info=True)
        return False, f"Reset error: {str(e)}"


def increment_failed_login(username: str) -> None:
    """
    Increment failed login attempts and lock account if threshold reached.
    
    Args:
        username: Username
    """
    supabase = init_supabase()
    if not supabase:
        return
    
    try:
        # Get current attempts
        res = supabase.table('admin_users').select(
            'id, failed_login_attempts'
        ).eq('username', username).execute()
        
        if not res.data:
            return
        
        user = res.data[0]
        attempts = user.get('failed_login_attempts', 0) + 1
        
        update_data = {'failed_login_attempts': attempts}
        
        # Lock account if threshold reached
        if attempts >= Config.MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.now() + timedelta(seconds=Config.ACCOUNT_LOCKOUT_DURATION)
            update_data['locked_until'] = locked_until.isoformat()
            update_data['is_active'] = False
            logger.warning(f"Account locked: {username} ({attempts} failed attempts)")
        
        supabase.table('admin_users').update(update_data).eq('id', user['id']).execute()
        
    except Exception as e:
        logger.error(f"Error incrementing failed login for {username}: {e}")


def get_pending_users() -> List[Dict]:
    """
    Get all users pending admin approval.
    
    Returns:
        List of user dictionaries
    """
    supabase = init_supabase()
    if not supabase:
        return []
    
    try:
        res = supabase.table('admin_users').select(
            'id, username, email, created_at'
        ).eq('is_verified', True).eq('is_approved', False).order('created_at').execute()
        
        return res.data if res.data else []
        
    except Exception as e:
        logger.error(f"Error getting pending users: {e}")
        return []


def approve_user(user_id: int, approved_by_id: int) -> Tuple[bool, str, Optional[Dict]]:
    """
    Approve user account.
    
    Args:
        user_id: User ID to approve
        approved_by_id: Admin user ID who is approving
        
    Returns:
        Tuple of (success: bool, message: str, user_info: Optional[Dict])
    """
    supabase = init_supabase()
    if not supabase:
        return False, "Database connection error", None
    
    try:
        # Get user info before approval
        res = supabase.table('admin_users').select(
            'id, username, email'
        ).eq('id', user_id).execute()
        
        if not res.data:
            return False, "User not found", None
        
        user = res.data[0]
        
        # Approve user
        supabase.table('admin_users').update({
            'is_approved': True,
            'is_active': True,
            'approved_by': approved_by_id,
            'approved_at': datetime.now().isoformat()
        }).eq('id', user_id).execute()
        
        logger.info(f"User approved: {user['username']} by admin {approved_by_id}")
        return True, "User approved successfully", user
        
    except Exception as e:
        logger.error(f"Error approving user {user_id}: {e}", exc_info=True)
        return False, f"Approval error: {str(e)}", None


def reject_user(user_id: int) -> Tuple[bool, str]:
    """
    Reject user account (delete from database).
    
    Args:
        user_id: User ID to reject
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    supabase = init_supabase()
    if not supabase:
        return False, "Database connection error"
    
    try:
        res = supabase.table('admin_users').select('username').eq('id', user_id).execute()
        
        if not res.data:
            return False, "User not found"
        
        username = res.data[0]['username']
        
        # Delete user
        supabase.table('admin_users').delete().eq('id', user_id).execute()
        
        logger.info(f"User rejected and deleted: {username}")
        return True, "User rejected successfully"
        
    except Exception as e:
        logger.error(f"Error rejecting user {user_id}: {e}", exc_info=True)
        return False, f"Rejection error: {str(e)}"


def get_all_admins() -> List[str]:
    """
    Get email addresses of all active admins for notifications.
    
    Returns:
        List of admin email addresses
    """
    supabase = init_supabase()
    if not supabase:
        return []
    
    try:
        res = supabase.table('admin_users').select(
            'email'
        ).eq('is_active', True).eq('is_approved', True).execute()
        
        return [user['email'] for user in res.data if user.get('email')]
        
    except Exception as e:
        logger.error(f"Error getting admin emails: {e}")
        return []


def get_admin_info(username: str) -> Optional[Dict]:
    """
    Get admin user info by username.
    
    Args:
        username: Username
        
    Returns:
        User dict or None
    """
    supabase = init_supabase()
    if not supabase:
        return None
    
    try:
        res = supabase.table('admin_users').select('id, username, email, is_approved').eq('username', username).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        logger.error(f"Error getting admin info: {e}")
        return None
