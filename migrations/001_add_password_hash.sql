-- ============================================
-- POD Automation System - Database Migration
-- Version: Quick Wins Phase 1
-- Date: 2026-01-21
-- ============================================

-- IMPORTANT: Run this in Supabase SQL Editor
-- This migration adds password_hash column for bcrypt support

-- ============================================
-- STEP 1: Add password_hash column
-- ============================================

ALTER TABLE admin_users 
ADD COLUMN IF NOT EXISTS password_hash TEXT;

COMMENT ON COLUMN admin_users.password_hash IS 'Bcrypt hashed password (replaces plaintext password column)';

-- ============================================
-- STEP 2: Verify migration
-- ============================================

-- Check if column exists
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'admin_users'
ORDER BY ordinal_position;

-- Expected output:
-- column_name  | data_type | is_nullable
-- -------------|-----------|------------
-- id           | bigint    | NO
-- username     | text      | YES
-- password     | text      | YES
-- name         | text      | YES
-- password_hash| text      | YES  ← NEW COLUMN

-- ============================================
-- STEP 3: Update existing users (MANUAL)
-- ============================================

-- DO NOT run this directly - you need to generate hashes first!
-- Use: python generate_password_hash.py

-- Example for each user:
-- UPDATE admin_users 
-- SET password_hash = '$2b$12$YOUR_GENERATED_HASH_HERE' 
-- WHERE username = 'admin';

-- ============================================
-- STEP 4: Verify login works (TESTING)
-- ============================================

-- Check which users have hashed passwords
SELECT 
    username,
    name,
    CASE 
        WHEN password_hash IS NOT NULL THEN '✅ Hashed'
        WHEN password IS NOT NULL THEN '⚠️ Plaintext'
        ELSE '❌ No password'
    END AS password_status
FROM admin_users;

-- ============================================
-- STEP 5: Cleanup (OPTIONAL - After migration complete)
-- ============================================

-- CAUTION: Only run this AFTER all users migrated to password_hash!
-- CAUTION: Backup database first!

-- Remove plaintext passwords
-- UPDATE admin_users 
-- SET password = NULL 
-- WHERE password_hash IS NOT NULL;

-- ============================================
-- ROLLBACK (Emergency Only)
-- ============================================

-- If you need to rollback (remove password_hash column):
-- ALTER TABLE admin_users DROP COLUMN IF EXISTS password_hash;

-- ============================================
-- Additional Security (RECOMMENDED)
-- ============================================

-- Enable Row Level Security (RLS) on admin_users table
-- ALTER TABLE admin_users ENABLE ROW LEVEL SECURITY;

-- Create policy to restrict access
-- CREATE POLICY "Admin users can only see own data" 
-- ON admin_users FOR SELECT 
-- USING (auth.uid()::text = id::text);

-- ============================================
-- Migration Complete!
-- ============================================

-- After running this migration:
-- 1. Test login with plaintext password (should still work - fallback mode)
-- 2. Generate hash for one user: python generate_password_hash.py
-- 3. Update that user's password_hash in database
-- 4. Test login with hashed password (should work)
-- 5. Check logs/app.log for "Login successful (hashed)"
-- 6. Repeat for all users
-- 7. Eventually remove plaintext passwords (Step 5)
