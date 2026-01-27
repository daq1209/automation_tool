import pytest
from src.utils.locales import get_text, TRANS

def test_get_text_default_en():
    """Test retrieving English text by default."""
    # Using a known key
    assert get_text("nav_dashboard", "en") == "Dashboard"

def test_get_text_vi():
    """Test retrieving Vietnamese text."""
    assert get_text("nav_dashboard", "vi") == "Tổng quan"

def test_get_text_fallback():
    """Test fallback to English if lang not found."""
    # 'fr' is not in TRANS, should look for 'en' or key
    assert get_text("nav_dashboard", "fr") == "Dashboard"

def test_get_text_missing_key():
    """Test returning key if not found."""
    assert get_text("non_existent_key", "en") == "non_existent_key"

def test_all_keys_have_en_vi():
    """Ensure all keys in TRANS have both 'en' and 'vi' entries."""
    for key, value in TRANS.items():
        assert "en" in value, f"Key '{key}' missing 'en'"
        assert "vi" in value, f"Key '{key}' missing 'vi'"
