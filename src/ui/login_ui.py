import streamlit as st
from src.repositories import db

def render_login():
    """Render login page"""
    st.title("POD Automation Login")
    
    with st.form("login_form"):
        username = st.text_input("Username:")
        password = st.text_input("Password:", type="password")
        submit = st.form_submit_button("Login", type="primary")
        
        if submit:
            if not username or not password:
                st.error("Please fill in both fields")
            else:
                if db.check_admin_login(username, password):
                    st.session_state['is_logged_in'] = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
