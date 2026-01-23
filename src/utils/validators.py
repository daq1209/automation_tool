"""
Input validation module for POD Automation System.

Provides Pydantic models and validation functions for data integrity.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, validator, ValidationError, EmailStr
from config import Config
import re


class ProductImport(BaseModel):
    """Validation model for product import data."""
    
    sku: str = Field(..., min_length=1, max_length=Config.MAX_SKU_LENGTH)
    title: str = Field(..., min_length=1, max_length=Config.MAX_TITLE_LENGTH)
    price: Optional[float] = Field(None, ge=Config.MIN_PRICE, le=Config.MAX_PRICE)
    description: Optional[str] = Field(None, max_length=Config.MAX_DESCRIPTION_LENGTH)
    images: Optional[List[str]] = None
    
    @validator('sku')
    def sku_must_be_valid(cls, v: str) -> str:
        """Validate SKU format."""
        if not v or not v.strip():
            raise ValueError('SKU cannot be empty or whitespace')
        # Remove any potentially dangerous characters
        if any(char in v for char in ['<', '>', '"', "'"]):
            raise ValueError('SKU contains invalid characters')
        return v.strip()
    
    @validator('title')
    def title_must_be_valid(cls, v: str) -> str:
        """Validate title."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('images')
    def images_must_be_urls(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate image URLs."""
        if v is None:
            return v
        
        valid_images = []
        for url in v:
            url = url.strip()
            if url and (url.startswith('http://') or url.startswith('https://')):
                valid_images.append(url)
        
        return valid_images if valid_images else None


class UserRegistration(BaseModel):
    """Validation model for user registration."""
    
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=Config.PASSWORD_MIN_LENGTH)
    password_confirm: str
    
    @validator('username')
    def username_must_be_valid(cls, v: str) -> str:
        """Validate username format."""
        if not v or not v.strip():
            raise ValueError('Username cannot be empty')
        
        # Only allow alphanumeric and underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        
        return v.strip().lower()
    
    @validator('password')
    def password_must_be_strong(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < Config.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {Config.PASSWORD_MIN_LENGTH} characters')
        
        if Config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if Config.PASSWORD_REQUIRE_NUMBER and not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        
        if Config.PASSWORD_REQUIRE_SPECIAL:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('password_confirm')
    def passwords_must_match(cls, v: str, values: dict) -> str:
        """Validate passwords match."""
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordReset(BaseModel):
    """Validation model for password reset request."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Validation model for password reset confirmation."""
    
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=Config.PASSWORD_MIN_LENGTH)
    new_password_confirm: str
    
    @validator('new_password')
    def password_must_be_strong(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < Config.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {Config.PASSWORD_MIN_LENGTH} characters')
        
        if Config.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if Config.PASSWORD_REQUIRE_NUMBER and not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        
        if Config.PASSWORD_REQUIRE_SPECIAL:
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
                raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('new_password_confirm')
    def passwords_must_match(cls, v: str, values: dict) -> str:
        """Validate passwords match."""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


def validate_sheet_structure(headers: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validate that Sheet has required columns.
    
    Args:
        headers: List of column headers from Sheet
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing_columns = set(Config.REQUIRED_COLUMNS) - set(headers)
    
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        return False, error_msg
    
    return True, None


def validate_product_data(product_dict: dict) -> tuple[bool, Optional[str], Optional[ProductImport]]:
    """
    Validate product data against schema.
    
    Args:
        product_dict: Dictionary with product data
        
    Returns:
        Tuple of (is_valid, error_message, validated_product)
    """
    try:
        validated = ProductImport(**product_dict)
        return True, None, validated
    except ValidationError as e:
        error_msg = '; '.join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
        return False, error_msg, None
