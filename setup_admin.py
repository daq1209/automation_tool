
import streamlit as st
import bcrypt
from src.repositories import db
from datetime import datetime

st.set_page_config(page_title="Admin Setup")

st.title("Admin Setup Script")

if st.button("Check Admins"):
    supabase = db.init_supabase()
    res = supabase.table('admin_users').select('*').execute()
    st.write(f"Found {len(res.data)} users.")
    st.dataframe(res.data)

if st.button("Create Admin User"):
    username = st.text_input("Username", value="admin")
    password = st.text_input("Password", value="admin123")
    email = st.text_input("Email", value="admin@example.com")
    
    if st.button("Create"):
        # Create super admin
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'is_verified': True,
            'is_approved': True,
            'is_active': True,
            'created_at': datetime.now().isoformat()
        }
        
        supabase = db.init_supabase()
        try:
            supabase.table('admin_users').insert(new_user).execute()
            st.success("Admin created!")
        except Exception as e:
            st.error(f"Error: {e}")

if st.button("Create Pending User"):
    username = "pending_user"
    email = "pending@example.com"
    password = "User123!"
    
    success, token = db.create_user(username, email, password)
    if success:
        st.success(f"Pending user created! Token: {token}")
        # Manually verify email so it shows up in pending list
        db.verify_email(token)
        st.info("User verified (but not approved). Should show in dashboard.")
    else:
        st.error(f"Error: {token}")
