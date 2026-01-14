import streamlit as st
from src.repositories import db

def render_login():
    st.markdown("<h2 style='text-align:center'>Login</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN"):
            if db.check_admin_login(u, p):
                st.session_state['is_logged_in'] = True
                st.rerun()
            else:
                st.error("Incorrect username or password")