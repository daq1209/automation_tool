"""
Email verification handler.

Processes email verification from URL query parameter.
"""

import streamlit as st
from src.repositories import db
from src.utils.email_service import email_service
from src.utils.logger import logger


def render_verify_email():
    """Handle email verification with token from URL."""
    st.title("📧 Email Verification")
    
    # Get token from URL query params
    token = st.query_params.get("verify")
    
    if not token:
        st.error("⚠️ No verification token provided")
        st.info("Please use the verification link sent to your email.")
        if st.button("← Back to Login"):
            st.query_params.clear()
            st.rerun()
        return
    
    # Verify email with token
    success, message = db.verify_email(token)
    
    if success:
        st.success(f"✅ {message}")
        st.balloons()
        
        st.info(
            "### What's Next?\n\n"
            "Your email has been verified successfully!\n\n"
            "**Next Step:** Your account is now pending admin approval.\n\n"
            "You will receive an email notification once your account has been approved by an administrator.\n\n"
            "After approval, you can login with your username and password."
        )
        
        # Notify all admins
        try:
            admin_emails = db.get_all_admins()
            if admin_emails:
                # Get user info for notification
                supabase = db.init_supabase()
                if supabase:
                    res = supabase.table('admin_users').select(
                        'username, email'
                    ).eq('verification_token', None).eq('is_verified', True).eq('is_approved', False).order('created_at.desc').limit(1).execute()
                    
                    if res.data:
                        new_user = res.data[0]
                        for admin_email in admin_emails:
                            email_service.send_admin_notification(
                                admin_email,
                                new_user['username'],
                                new_user['email']
                            )
                        logger.info(f"Admin notifications sent for new user: {new_user['username']}")
        except Exception as e:
            logger.error(f"Failed to send admin notifications: {e}")
        
        if st.button("← Go to Login", type="primary"):
            st.query_params.clear()
            st.rerun()
            
    else:
        st.error(f"❌ Verification Failed")
        st.warning(message)
        
        st.info(
            "**Common Issues:**\n\n"
            "• Link expired (24 hours limit)\n"
            "• Link already used\n"
            "• Invalid token\n\n"
            "If you need a new verification link, please register again or contact support."
        )
        
        if st.button("← Back to Registration"):
            st.query_params.clear()
            st.rerun()
