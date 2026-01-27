import streamlit as st
from src.utils.common import local_css
from src.ui import login_ui, main_ui, verify_email, reset_password

# 1. Cấu hình trang
st.set_page_config(page_title="POD Automation Environment", layout="wide", initial_sidebar_state="auto")

# 2. Load CSS
local_css("style.css")

# 3. Quản lý trạng thái đăng nhập
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

# 4. Điều hướng với URL parameters
# Check for special pages (email verification, password reset)
if "verify" in st.query_params:
    verify_email.render_verify_email()
elif "reset" in st.query_params:
    reset_password.render_reset_password()
elif st.session_state['is_logged_in']:
    main_ui.render_dashboard()
else:
    login_ui.render_login()
