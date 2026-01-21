# Migration Guide: Quick Wins Implementation

## Overview
This guide helps you migrate from the old codebase to the improved version with password hashing, structured logging, and configuration constants.

---

## 1. Password Hashing Migration

### Step 1: Update Supabase Schema

**Current `admin_users` table structure:**
```
- id (bigint)
- username (text)
- password (text)  ← Plaintext (INSECURE)
- name (text)
```

**Run this SQL in Supabase SQL Editor:**

```sql
-- Add new column for hashed passwords
ALTER TABLE admin_users 
ADD COLUMN password_hash TEXT;

-- Verify column was added
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'admin_users';
```

**Expected result after migration:**
```
- id (bigint)
- username (text)
- password (text)  ← Will be deprecated after migration
- name (text)
- password_hash (text)  ← NEW - Secure bcrypt hash
```

### Step 2: Generate Password Hashes
Use the provided script to generate bcrypt hashes:

```bash
python generate_password_hash.py
```

Enter each user's plaintext password, copy the generated hash.

### Step 3: Update Supabase Records
For each admin user, run:

```sql
UPDATE admin_users 
SET password_hash = '$2b$12$your_generated_hash_here' 
WHERE username = 'admin_username';
```

### Step 4: Verify Migration
1. Try logging in with a hashed password user
2. Check `logs/app.log` - should see "Login successful (hashed)"
3. Old plaintext users will still work (fallback mode)

### Step 5: Remove Plaintext Passwords (Optional)
After all users migrated:

```sql
UPDATE admin_users SET password = NULL WHERE password_hash IS NOT NULL;
```

---

## 2. Configuration Constants

### What Changed
Hard-coded values are now in `config.py`:

**Before:**
```python
MAX_RETRIES = 5  # In woo.py
time.sleep(0.5)  # In importer.py
chunk_size = 50  # In importer.py
```

**After:**
```python
from config import Config

Config.MAX_RETRIES  # 5
Config.PHASE_DELAY  # 0.5
Config.CHUNK_SIZE   # 50
```

### Customization
To change behavior, edit `config.py`:

```python
class Config:
    WORKER_COUNT: int = 30  # Increase for faster processing
    BATCH_SIZE: int = 100   # Larger batches
    RETRY_DELAY: int = 3    # Longer delays
```

---

## 3. Structured Logging

### Where Logs Are Stored
- **Location:** `logs/app.log`
- **Max Size:** 10 MB (then rotates)
- **Backups:** 5 files kept

### Log Levels
- **INFO:** Normal operations (imports, logins)
- **WARNING:** Recoverable issues (retry attempts, fallback to plaintext)
- **ERROR:** Failures (DB errors, bcrypt errors)

### Viewing Logs
```bash
# View latest logs
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# View specific user logins
grep "Login attempt" logs/app.log
```

### Example Log Entries
```
2026-01-21 10:15:23 - pod_automation - INFO - Login attempt for user: admin
2026-01-21 10:15:23 - pod_automation - INFO - Login successful (hashed): admin
2026-01-21 10:16:45 - pod_automation - WARNING - Post batch attempt 1 failed: Connection timeout
2026-01-21 10:17:02 - pod_automation - ERROR - Bcrypt error for user123: Invalid salt
```

---

## 4. Input Validation (Validators)

### What's Validated
- SKU: 1-100 chars, no HTML tags
- Title: 1-200 chars, non-empty
- Price: 0.00 to 999,999.99
- Images: Must start with http:// or https://

### Using Validators

**In your code:**
```python
from src.utils.validators import validate_product_data, validate_sheet_structure

# Validate sheet structure
is_valid, error = validate_sheet_structure(headers)
if not is_valid:
    st.error(f"Sheet validation failed: {error}")

# Validate product data
product = {'sku': 'ABC123', 'title': 'Test Product', 'price': 19.99}
is_valid, error, validated = validate_product_data(product)
if is_valid:
    # Use validated.sku, validated.title, etc.
    pass
```

---

## 5. Testing Checklist

### Password Hashing ✅
- [ ] Hash generated for all users
- [ ] Login works with hashed password
- [ ] Old plaintext still works (fallback)
- [ ] Logs show "Login successful (hashed)"

### Configuration ✅
- [ ] App runs without errors
- [ ] Config values can be changed
- [ ] Import speed same or better

### Logging ✅
- [ ] `logs/app.log` created automatically
- [ ] Log entries appear during import
- [ ] Login attempts logged
- [ ] Log file rotates at 10MB

### Validation ✅
- [ ] Invalid SKU rejected
- [ ] Empty title rejected
- [ ] Negative price rejected
- [ ] Non-URL images filtered out

---

## 6. Rollback Instructions

If issues occur:

### Revert `db.py`
```bash
git checkout HEAD -- src/repositories/db.py
```

Or manually restore old login function.

### Disable Logging
In each file, comment out:
```python
# from src.utils.logger import logger
# logger.info(...)
```

### Revert Config
Replace `Config.MAX_RETRIES` with hard-coded `5`, etc.

---

## 7. Support & Troubleshooting

### Common Issues

**Login fails after migration:**
- Check password_hash format (should start with `$2b$`)
- Verify bcrypt installed: `pip list | grep bcrypt`
- Check logs for detailed error

**Import slower:**
- Check Config.WORKER_COUNT (increase if needed)
- Check Config.RETRY_DELAY (reduce if stable connection)

**Logs not created:**
- Check folder permissions for `logs/`
- Verify logger import not commented out

---

## 8. Next Steps

After successful migration:

1. **Monitor logs** for a few days
2. **Backup database** before removing plaintext passwords
3. **Add more validators** if needed (see validators.py)
4. **Consider Phase 2 improvements** (see SYSTEM_ASSESSMENT.md)

---

*Generated: 2026-01-21*
