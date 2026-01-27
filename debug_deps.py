import sys
print(f"Python Executable: {sys.executable}")
print("Attempting to import email_validator...")
try:
    import email_validator
    print(f"SUCCESS: email_validator version {email_validator.version_string()}")
except ImportError as e:
    print(f"FAILED: {e}")

print("Attempting to import pydantic and use EmailStr...")
try:
    from pydantic import BaseModel, EmailStr, Field
    class TestModel(BaseModel):
        email: EmailStr
    
    m = TestModel(email="test@example.com")
    print(f"SUCCESS: Pydantic EmailStr validation working. {m}")
except Exception as e:
    print(f"FAILED: {e}")
