"""
Quick email test script.
Run: streamlit run test_email.py
"""

import streamlit as st
from src.utils.email_service import email_service

st.set_page_config(page_title="📧 Email Test", layout="centered")

st.title("📧 Email Service Test")
st.caption("Test your Gmail SMTP configuration")

st.info("✅ SMTP configured: daqtheedgelord@gmail.com")

# Test Verification Email
st.subheader("1️⃣ Test Verification Email")
recipient1 = st.text_input("Recipient email:", value="daqtheedgelord@gmail.com", key="verify")

if st.button("Send Verification Email", type="primary"):
    with st.spinner("Sending..."):
        success, msg = email_service.send_verification_email(
            recipient1,
            "testuser",
            "test-token-12345"
        )
    if success:
        st.success(f"✅ Verification email sent to {recipient1}!")
        st.balloons()
    else:
        st.error(f"❌ Failed: {msg}")

st.write("---")

# Test Password Reset Email
st.subheader("2️⃣ Test Password Reset Email")
recipient2 = st.text_input("Recipient email:", value="daqtheedgelord@gmail.com", key="reset")

if st.button("Send Password Reset Email", type="primary"):
    with st.spinner("Sending..."):
        success, msg = email_service.send_password_reset_email(
            recipient2,
            "testuser",
            "reset-token-67890"
        )
    if success:
        st.success(f"✅ Password reset email sent to {recipient2}!")
        st.balloons()
    else:
        st.error(f"❌ Failed: {msg}")

st.write("---")
st.caption("Check your inbox (and spam folder) for test emails")
