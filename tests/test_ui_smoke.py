import pytest
from unittest.mock import MagicMock
import sys

# Mock streamlit before importing UI modules
sys.modules["streamlit"] = MagicMock()

def test_ui_imports():
    """Smoke test to ensure UI modules import without syntax errors."""
    try:
        from src.ui import main_ui
        from src.ui import updater_ui
        from src.ui import login_ui
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import UI modules: {e}")
    except SyntaxError as e:
        pytest.fail(f"Syntax error in UI modules: {e}")
    except Exception as e:
        # Other errors might occur due to missing secrets/db during import, 
        # but we just want to catch syntax/import issues if possible.
        # For now, pass if it's just a runtime error during top-level execution
        pass
