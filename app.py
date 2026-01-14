import streamlit as st
from src.utils.common import local_css
from src.ui import login_ui, main_ui

# 1. Cấu hình trang
st.set_page_config(page_title="POD Automation Environment", layout="wide")

# 2. Load CSS
local_css("style.css")

# 3. Quản lý trạng thái đăng nhập
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

# 4. Điều hướng
if st.session_state['is_logged_in']:
    main_ui.render_dashboard()
else:
    login_ui.render_login()