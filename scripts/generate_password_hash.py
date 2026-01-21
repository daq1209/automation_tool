"""
Password Hash Generator for POD Automation System.

Use this script to generate bcrypt password hashes for Supabase migration.
"""

import bcrypt

def generate_password_hash(password: str) -> str:
    """
    Generate bcrypt hash from plaintext password.
    
    Args:
        password: Plaintext password
        
    Returns:
        Bcrypt hash string
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


if __name__ == "__main__":
    print("=" * 60)
    print("POD Automation - Password Hash Generator")
    print("=" * 60)
    print()
    print("This script generates bcrypt password hashes for Supabase.")
    print("Copy the generated hash to the 'password_hash' column in admin_users table.")
    print()
    
    while True:
        password = input("Enter password (or 'q' to quit): ")
        
        if password.lower() == 'q':
            print("Goodbye!")
            break
        
        if not password:
            print("❌ Password cannot be empty!\n")
            continue
        
        # Generate hash
        hashed = generate_password_hash(password)
        
        print()
        print("✅ Password hash generated successfully!")
        print("-" * 60)
        print(f"Hash: {hashed}")
        print("-" * 60)
        print()
        print("📋 SQL Query to update Supabase:")
        print(f"UPDATE admin_users SET password_hash = '{hashed}' WHERE username = 'YOUR_USERNAME';")
        print()
