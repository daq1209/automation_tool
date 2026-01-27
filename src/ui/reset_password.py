"""
Password reset handler.

Processes password reset from URL query parameter.
"""

import streamlit as st
from src.repositories import db
from src.utils.validators import PasswordResetConfirm, ValidationError
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


def render_reset_password():
    """Handle password reset with token from URL."""
    st.title("Reset Your Password")
    
    # Get token from URL query params
    token = st.query_params.get("reset")
    
    if not token:
        st.error("No reset token provided")
        st.info("Please use the reset link sent to your email.")
        if st.button("← Back to Login"):
            st.query_params.clear()
            st.rerun()
        return
    
    st.info("Enter your new password below:")
    
    with st.form("reset_password_form"):
        new_password = st.text_input(
            "New Password:",
            type="password",
            placeholder="Enter your new password"
        )
        
        # Password strength indicator
        if new_password:
            score, feedback = check_password_strength(new_password)
            colors = ['[Very Weak]', '[Weak]', '[Medium]', '[Strong]', '[Strong]']
            st.caption(f"{colors[score]} Strength: {feedback}")
        
        new_password_confirm = st.text_input(
            "Confirm New Password:",
            type="password",
            placeholder="Re-enter your new password"
        )
        
        submit = st.form_submit_button("Reset Password", type="primary", use_container_width=True)
        
        if submit:
            if not new_password or not new_password_confirm:
                st.error("Please fill in both fields")
                return
            
            # Validate with Pydantic
            try:
                validated = PasswordResetConfirm(
                    token=token,
                    new_password=new_password,
                    new_password_confirm=new_password_confirm
                )
                
                # Reset password
                success, message = db.reset_password(validated.token, validated.new_password)
                
                if success:
                    st.success("Password Reset Successful!")
                    st.balloons()
                    
                    st.info(
                        "### Success!\n\n"
                        "Your password has been reset successfully.\n\n"
                        "You can now login with your new password."
                    )
                    
                    logger.info("Password reset completed successfully")
                    
                    if st.button("← Go to Login", type="primary"):
                        st.query_params.clear()
                        st.rerun()
                else:
                    st.error(f"Reset Failed: {message}")
                    st.warning(
                        "**Common Issues:**\n\n"
                        "• Link expired (1 hour limit)\n"
                        "• Link already used\n"
                        "• Invalid token\n\n"
                        "Please request a new password reset link."
                    )
                    
            except ValidationError as e:
                errors = e.errors()
                for error in errors:
                    field = error['loc'][0]
                    msg = error['msg']
                    st.error(f"{field}: {msg}")
    
    st.write("")
    st.write("")
    if st.button("← Back to Login"):
        st.query_params.clear()
        st.rerun()
