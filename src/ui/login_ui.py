"""
Login UI with Registration and Password Reset tabs.
"""

import streamlit as st
import re
from src.repositories import db
from src.utils.email_service import email_service
from src.utils.validators import UserRegistration, PasswordReset, ValidationError
from src.utils.logger import logger
from config import Config


def check_password_strength(password: str) -> tuple[int, str]:
    """
    Check password strength and return score + feedback.
    
    Returns:
        Tuple of (score: 0-4, feedback: str)
    """
    score = 0
    feedback = []
    
    if len(password) >= Config.PASSWORD_MIN_LENGTH:
        score += 1
    else:
        feedback.append(f"At least {Config.PASSWORD_MIN_LENGTH} characters")
    
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("One uppercase letter")
    
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("One lowercase letter")
    
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("One number")
    
    if score == 4:
        return score, "Strong"
    elif score == 3:
        return score, "Good (missing: " + ", ".join(feedback) + ")"
    elif score == 2:
        return score, "Weak (missing: " + ", ".join(feedback) + ")"
    else:
        return score, "Too weak (missing: " + ", ".join(feedback) + ")"


def render_login_form():
    """Render login form."""
    st.markdown("### 🔐 Login to Your Account")
    
    with st.form("login_form"):
        username = st.text_input("Username or Email:", placeholder="Enter your username")
        password = st.text_input("Password:", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            submit = st.form_submit_button("Login", type="primary", use_container_width=True)
        with col2:
            if st.form_submit_button("Clear", use_container_width=True):
                st.rerun()
        
        if submit:
            if not username or not password:
                st.error("⚠️ Please fill in both fields")
            else:
                # Try login
                if db.check_admin_login(username, password):
                    st.session_state['is_logged_in'] = True
                    st.session_state['username'] = username
                    st.success("✅ Login successful!")
                    logger.info(f"User logged in: {username}")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials or account inactive")
                    logger.warning(f"Failed login attempt: {username}")


def render_registration_form():
    """Render registration form."""
    st.markdown("### 📝 Create New Account")
    st.info("ℹ️ You will need to verify your email and wait for admin approval before you can login.")
    
    with st.form("registration_form"):
        username = st.text_input(
            "Username:", 
            placeholder="Choose a unique username (letters, numbers, underscore)",
            help="3-50 characters, alphanumeric and underscore only"
        )
        
        email = st.text_input(
            "Email:", 
            placeholder="your.email@example.com",
            help="Must be a valid email address"
        )
        
        password = st.text_input(
            "Password:", 
            type="password",
            placeholder="Choose a strong password"
        )
        
        # Password strength indicator
        if password:
            score, feedback = check_password_strength(password)
            colors = ['🔴', '🟠', '🟡', '🟢', '🟢']
            st.caption(f"{colors[score]} Strength: {feedback}")
        
        password_confirm = st.text_input(
            "Confirm Password:", 
            type="password",
            placeholder="Re-enter your password"
        )
        
        terms = st.checkbox("I agree to the Terms of Service and Privacy Policy")
        
        submit = st.form_submit_button("Create Account", type="primary", use_container_width=True)
        
        if submit:
            if not username or not email or not password or not password_confirm:
                st.error("⚠️ Please fill in all fields")
                return
            
            if not terms:
                st.error("⚠️ You must agree to the Terms of Service")
                return
            
            # Validate with Pydantic
            try:
                validated = UserRegistration(
                    username=username,
                    email=email,
                    password=password,
                    password_confirm=password_confirm
                )
                
                # Create user in database
                success, result = db.create_user(
                    validated.username,
                    validated.email,
                    validated.password
                )
                
                if success:
                    verification_token = result
                    
                    # Send verification email
                    email_success, email_msg = email_service.send_verification_email(
                        validated.email,
                        validated.username,
                        verification_token
                    )
                    
                    if email_success:
                        st.success("✅ Account created successfully!")
                        st.info(
                            f"📧 A verification email has been sent to **{validated.email}**\n\n"
                            "Please check your inbox (and spam folder) and click the verification link.\n\n"
                            "⏰ The link will expire in 24 hours."
                        )
                        logger.info(f"User registered: {validated.username}")
                    else:
                        st.warning(
                            "⚠️ Account created but email failed to send.\n\n"
                            f"Error: {email_msg}\n\n"
                            "Please contact admin to manually verify your account."
                        )
                else:
                    st.error(f"❌ Registration failed: {result}")
                    
            except ValidationError as e:
                errors = e.errors()
                for error in errors:
                    field = error['loc'][0]
                    message = error['msg']
                    st.error(f"❌ {field}: {message}")


def render_forgot_password_form():
    """Render forgot password form."""
    st.markdown("### 🔑 Reset Your Password")
    st.info("ℹ️ Enter your email address and we'll send you a link to reset your password.")
    
    with st.form("forgot_password_form"):
        email = st.text_input(
            "Email Address:", 
            placeholder="your.email@example.com"
        )
        
        submit = st.form_submit_button("Send Reset Link", type="primary", use_container_width=True)
        
        if submit:
            if not email:
                st.error("⚠️ Please enter your email address")
                return
            
            # Validate email format
            try:
                validated = PasswordReset(email=email)
                
                # Request password reset
                success, message, reset_token = db.request_password_reset(validated.email)
                
                if success and reset_token:
                    # Send reset email
                    # Get username for email (optional)
                    supabase = db.init_supabase()
                    if supabase:
                        res = supabase.table('admin_users').select('username').eq('email', validated.email).execute()
                        username = res.data[0]['username'] if res.data else 'User'
                    else:
                        username = 'User'
                    
                    email_success, email_msg = email_service.send_password_reset_email(
                        validated.email,
                        username,
                        reset_token
                    )
                    
                    if email_success:
                        st.success(
                            "✅ Password reset link sent!\n\n"
                            f"📧 If an account exists with **{validated.email}**, "
                            "you will receive a password reset link.\n\n"
                            "⏰ The link will expire in 1 hour."
                        )
                        logger.info(f"Password reset requested for: {validated.email}")
                    else:
                        st.error(f"❌ Failed to send email: {email_msg}")
                else:
                    # Always show same message (prevent email enumeration)
                    st.success(
                        "✅ Password reset link sent!\n\n"
                        f"📧 If an account exists with **{validated.email}**, "
                        "you will receive a password reset link.\n\n"
                        "⏰ The link will expire in 1 hour."
                    )
                    
            except ValidationError as e:
                st.error(f"❌ Invalid email address")


def render_login():
    """Main login page with tabs."""
    st.title("🔐 POD Automation System")
    st.caption("Version 13.0 - User Management Enabled")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Register", "🔑 Forgot Password"])
    
    with tab1:
        st.write("")  # Spacing
        render_login_form()
        
    with tab2:
        st.write("")  # Spacing
        render_registration_form()
        
    with tab3:
        st.write("")  # Spacing
        render_forgot_password_form()
    
    # Footer
    st.write("")
    st.write("")
    st.markdown("---")
    st.caption("🔒 Secure authentication powered by bcrypt and email verification")
