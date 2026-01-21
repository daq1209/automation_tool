# Tests

This directory contains unit tests for the POD Automation System.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_validators.py
```

## Test Structure

- `test_validators.py` - Input validation tests
- `test_db.py` - Database connection tests (TODO)
- `test_importer.py` - Import logic tests (TODO)
- `test_deleter.py` - Delete logic tests (TODO)

## Writing Tests

Follow pytest conventions:
- Test files must start with `test_`
- Test functions must start with `test_`
- Use fixtures for common setup
