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
