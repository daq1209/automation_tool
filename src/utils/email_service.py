"""
Email service for POD Automation Environment.

Handles sending verification and password reset emails via SMTP Gmail.
"""

import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Tuple, Optional
from src.utils.logger import logger
from config import Config


class EmailService:
    """Email service using SMTP Gmail."""
    
    def __init__(self):
        """Initialize email service with credentials from Streamlit secrets."""
        try:
            self.smtp_host = st.secrets.get("email", {}).get("smtp_host", Config.SMTP_HOST)
            self.smtp_port = st.secrets.get("email", {}).get("smtp_port", Config.SMTP_PORT)
            self.smtp_user = st.secrets.get("email", {}).get("smtp_user", "")
            self.smtp_password = st.secrets.get("email", {}).get("smtp_password", "")
            self.from_email = st.secrets.get("email", {}).get("from_email", self.smtp_user)
            self.app_url = st.secrets.get("email", {}).get("app_url", "http://localhost:8501")
            
            if not self.smtp_user or not self.smtp_password:
                logger.warning("Email credentials not configured in secrets.toml")
                
        except Exception as e:
            logger.error(f"Failed to initialize email service: {e}")
    
    def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str = "") -> Tuple[bool, str]:
        """
        Send email via SMTP.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text fallback (optional)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.smtp_user or not self.smtp_password:
            return False, "Email service not configured"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"POD Automation <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach plain text and HTML
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if Config.SMTP_USE_TLS:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True, "Email sent successfully"
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False, "Email authentication failed. Check credentials."
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False, f"Failed to send email: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error sending email: {e}", exc_info=True)
            return False, f"Unexpected error: {str(e)}"
    
    def send_verification_email(self, to_email: str, username: str, token: str) -> Tuple[bool, str]:
        """
        Send email verification email.
        
        Args:
            to_email: User's email address
            username: User's username
            token: Verification token
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        verification_link = f"{self.app_url}?verify={token}"
        
        subject = "Verify Your POD Automation Account"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; 
                           color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>POD Automation</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Thank you for registering! Please verify your email address by clicking the button below:</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy this link to your browser:</p>
                    <p style="word-break: break-all; font-size: 12px; color: #666;">{verification_link}</p>
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    <p>After verification, your account will be pending admin approval before you can login.</p>
                    <p>If you didn't create this account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>POD Automation Environment &copy; 2026</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        POD Automation - Email Verification
        
        Hi {username},
        
        Thank you for registering! Please verify your email address by clicking the link below:
        
        {verification_link}
        
        This link will expire in 24 hours.
        
        After verification, your account will be pending admin approval before you can login.
        
        If you didn't create this account, please ignore this email.
        
        ---
        POD Automation Environment © 2026
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, username: str, token: str) -> Tuple[bool, str]:
        """
        Send password reset email.
        
        Args:
            to_email: User's email address
            username: User's username
            token: Reset token
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        reset_link = f"{self.app_url}?reset={token}"
        
        subject = "Reset Your POD Automation Password"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #FF9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
               .button {{ display: inline-block; padding: 12px 24px; background-color: #FF9800; 
                           color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>We received a request to reset your password. Click the button below to proceed:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy this link to your browser:</p>
                    <p style="word-break: break-all; font-size: 12px; color: #666;">{reset_link}</p>
                    <p><strong>This link will expire in 1 hour.</strong></p>
                    <p>If you didn't request a password reset, you can safely ignore this email. 
                       Your password will not be changed.</p>
                </div>
                <div class="footer">
                    <p>POD Automation System &copy; 2026</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        POD Automation - Password Reset
        
        Hi {username},
        
        We received a request to reset your password. Click the link below to proceed:
        
        {reset_link}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, you can safely ignore this email.
        
        ---
        POD Automation System © 2026
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_approval_notification(self, to_email: str, username: str) -> Tuple[bool, str]:
        """
        Send account approval notification to user.
        
        Args:
            to_email: User's email address
            username: User's username
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        subject = "Your POD Automation Account Has Been Approved!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #2196F3; 
                           color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Account Approved!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Great news! Your POD Automation account has been approved by an administrator.</p>
                    <p>You can now login and start using the system:</p>
                    <p style="text-align: center;">
                        <a href="{self.app_url}" class="button">Go to Login</a>
                    </p>
                    <p><strong>Your username:</strong> {username}</p>
                    <p>Welcome aboard!</p>
                </div>
                <div class="footer">
                    <p>POD Automation System &copy; 2026</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        POD Automation - Account Approved
        
        Hi {username},
        
        Great news! Your POD Automation account has been approved by an administrator.
        
        You can now login at: {self.app_url}
        
        Your username: {username}
        
        Welcome aboard!
        
        ---
        POD Automation System © 2026
        """
        
        return self._send_email(to_email, subject, html_content, text_content)
    
    def send_admin_notification(self, admin_email: str, new_username: str, new_user_email: str) -> Tuple[bool, str]:
        """
        Send notification to admin about new user pending approval.
        
        Args:
            admin_email: Admin's email address
            new_username: New user's username
            new_user_email: New user's email
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        subject = "New User Pending Approval - POD Automation"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #9C27B0; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #9C27B0; 
                           color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .info-box {{ background-color: #fff; padding: 15px; border-left: 4px solid #9C27B0; margin: 15px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New User Registration</h1>
                </div>
                <div class="content">
                    <h2>Admin Action Required</h2>
                    <p>A new user has completed email verification and is pending your approval:</p>
                    <div class="info-box">
                        <p><strong>Username:</strong> {new_username}</p>
                        <p><strong>Email:</strong> {new_user_email}</p>
                        <p><strong>Status:</strong> Pending Approval</p>
                    </div>
                    <p>Please login to the admin dashboard to review and approve or reject this user:</p>
                    <p style="text-align: center;">
                        <a href="{self.app_url}" class="button">Go to Admin Dashboard</a>
                    </p>
                </div>
                <div class="footer">
                    <p>POD Automation System &copy; 2026</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        POD Automation - New User Pending Approval
        
        Admin Action Required
        
        A new user has completed email verification and is pending your approval:
        
        Username: {new_username}
        Email: {new_user_email}
        Status: Pending Approval
        
        Please login to the admin dashboard to review and approve or reject this user:
        {self.app_url}
        
        ---
        POD Automation System © 2026
        """
        
        return self._send_email(admin_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()
