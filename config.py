"""
Configuration constants for POD Automation System.

This module centralizes all configuration values to avoid magic numbers
and hard-coded values throughout the codebase.
"""

class Config:
    """Application configuration constants."""
    
    # API Retry Settings
    MAX_RETRIES: int = 5
    RETRY_DELAY: int = 2  # seconds
    
    # Batch Processing
    BATCH_SIZE: int = 50
    WORKER_COUNT: int = 20
    CHUNK_SIZE: int = 50
    
    # Timeouts
    IMPORT_TIMEOUT: int = 300  # 5 minutes
    API_TIMEOUT: int = 30  # 30 seconds
    
    # Sleep Delays
    PHASE_DELAY: float = 0.5  # seconds between phases
    WORKER_COMPLETION_DELAY: int = 2  # seconds after workers complete
    
    # Logging
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT: int = 5
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Email Settings (SMTP Gmail)
    EMAIL_PROVIDER: str = "smtp"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_NUMBER: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_DURATION: int = 900  # 15 minutes in seconds
    
    # Token Expiry
    VERIFICATION_TOKEN_EXPIRY: int = 86400  # 24 hours in seconds
    RESET_TOKEN_EXPIRY: int = 3600  # 1 hour in seconds
    
    # Rate Limiting
    MAX_REGISTRATION_PER_HOUR: int = 5
    MAX_PASSWORD_RESET_PER_HOUR: int = 3
    
    # Sheet Column Names (for validation)
    REQUIRED_COLUMNS: list = [
        'Check_update',
        'ID',
        'Type',
        'Name',
        'Published',
        'Regular price',
        'Images'
    ]
    
    # Product Validation
    MAX_SKU_LENGTH: int = 100
    MAX_TITLE_LENGTH: int = 200
    MAX_DESCRIPTION_LENGTH: int = 10000
    MIN_PRICE: float = 0.0
    MAX_PRICE: float = 999999.99
