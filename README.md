# POD Automation System 🚀

> **Version:** V13.0 Enterprise (Cloud Deployment & Enhanced Sync Logic)  
> **Last Updated:** 2026-01-22

An internal automation system for synchronizing product data between Google Sheets and WordPress/WooCommerce via custom APIs. Now successfully deployed on **Streamlit Cloud**.

---

## 📚 Documentation

- **[System Overview](docs/SYSTEM_OVERVIEW.md)** - Architecture & technical details
- **[System Assessment](docs/SYSTEM_ASSESSMENT.md)** - Weaknesses & improvement plan
- **[Migration Guide](docs/MIGRATION_GUIDE.md)** - How to upgrade to latest version

---

## ✨ Recent Improvements (Phase 1 - Quick Wins)

✅ **Security Hardening**
- Password hashing with bcrypt
- Input validation with Pydantic
- Structured logging for audit trail

✅ **Code Quality**
- Centralized configuration (`config.py`)
- Removed magic numbers
- Better error handling

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment (if using one)
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/Mac

# Install packages
pip install -r requirements.txt
```

### 2. Configure Secrets

Edit `.streamlit/secrets.toml`:

```toml
[supabase]
url = "YOUR_SUPABASE_URL"
key = "YOUR_SUPABASE_KEY"

[google]
service_account_base64 = "YOUR_BASE64_ENCODED_SERVICE_ACCOUNT"
```

### 3. Setup Database

Run SQL migrations in Supabase (see `docs/MIGRATION_GUIDE.md`)

### 4. Run Application

```bash
streamlit run app.py
```

Access at: `http://localhost:8501`

---

## 📁 Project Structure

```
test/
├── app.py                      # Main Streamlit entry point
├── config.py                   # Configuration constants
├── generate_password_hash.py   # Password hash generator
├── style.css                   # Custom CSS styles
├── .streamlit/
│   └── secrets.toml           # Sensitive credentials
├── src/
│   ├── repositories/          # Data access layer
│   │   ├── db.py             # Supabase & Google Sheets
│   │   └── woo.py            # WordPress API client
│   ├── services/              # Business logic
│   │   ├── importer.py       # Product import
│   │   ├── deleter.py        # Product deletion
│   │   └── checker.py        # Two-way sync
│   ├── ui/                    # Streamlit UI components
│   │   ├── login_ui.py       # Login screen
│   │   └── main_ui.py        # Dashboard
│   └── utils/                 # Helper functions
│       ├── common.py          # Utilities
│       ├── logger.py          # Logging setup
│       └── validators.py      # Input validation
├── docs/                      # Documentation
├── logs/                      # Application logs
├── php/                       # WordPress snippet (reference only)
└── sheet/                     # Google Sheets CSV backups (reference only)
```

---

## 🔑 Key Features

### Import Pipeline
- **Two-phase processing:** Text data first, images later
- **Multi-threading:** 20+ concurrent workers
- **Queue system:** Background image processing
- **Deduplication:** Prevent duplicate images
- **Auto-sync:** Updates Google Sheet statuses

### Smart Image Sync (New in V13)
- **Status Logic:**
  - `Done`: Both Title AND Slug match the new values.
  - `Holding`: Slug still matches the old value (pending update).
  - `Error`: Mismatch or update failure.
- **Bi-directional Check:** strict validation of Title & Slug.

### Delete Tool
- **Batch deletion:** Products & media
- **Two-factor confirmation:** Prevent accidental deletion
- **Sheet sync:** Updates status to "Holding" / "-1"

### Security
- **Dynamic secret keys:** No hard-coded credentials
- **Bcrypt hashing:** Secure password storage
- **Input validation:** Prevent injection attacks
- **Audit logging:** Track all actions

---

## 🛠️ Configuration

Edit `config.py` to customize behavior:

```python
class Config:
    # Performance tuning
    WORKER_COUNT: int = 20       # Concurrent workers
    BATCH_SIZE: int = 50         # Products per batch
    RETRY_DELAY: int = 2         # Seconds between retries
    
    # Timeouts
    IMPORT_TIMEOUT: int = 300    # 5 minutes
    API_TIMEOUT: int = 30        # 30 seconds
```

---

## 📊 Monitoring & Logs

### View Logs

```bash
# Real-time log monitoring
tail -f logs/app.log

# Search for errors
grep "ERROR" logs/app.log

# View login attempts
grep "Login attempt" logs/app.log
```

### Log Levels
- **INFO:** Normal operations
- **WARNING:** Retries, fallbacks
- **ERROR:** Failures requiring attention

---

## 🧪 Testing

### Generate Password Hash
```bash
python generate_password_hash.py
```

### Validate Sheet Structure
Check that Google Sheet has required columns:
- `Check_update`, `ID`, `Name`, `Published`, `Regular price`, `Images`

### Test Import (Dry Run)
1. Import 1-2 products first
2. Check `logs/app.log` for issues
3. Verify products appear in WordPress
4. Scale up to full imports

---

## 🐛 Troubleshooting

### Login Fails
- Check `password_hash` column in Supabase
- Verify bcrypt installed: `pip list | grep bcrypt`
- Check `logs/app.log` for errors

### Import Slow
- Increase `Config.WORKER_COUNT` (max ~30)
- Check network speed to WordPress
- Verify WordPress server resources

### Sheet Sync Issues
- Verify Google Service Account has edit access
- Check API quota (60 requests/min)
- Look for rate limit errors in logs

---

## 🔄 Workflow

### Typical Import Workflow
1. **Update Google Sheet** with product data
2. **Open Streamlit app** → Login
3. **Select website** from dropdown
4. **Load data** from Sheet
5. **Preview** products to import
6. **Click "Run Import"**
7. **Monitor progress** (Phase 1 → Phase 2)
8. **Verify** on WordPress site

### Typical Delete Workflow
1. **Search products** by SKU or ID
2. **Select items** to delete
3. **Enable deletion** (checkbox)
4. **Confirm deletion** (security input)
5. **Execute** → Products & media removed
6. **Sheet auto-syncs** (status → "Holding")

---

## 📝 Changelog

### 2026-01-22 - V13.0 Cloud Deployment
- 🚀 **Deployed to Streamlit Cloud:** Migrated from Google Colab for 24/7 stability.
- ✨ **Enhanced UpdateImage Logic:** Added strict `Done`/`Holding`/`Error` status based on Title & Slug verification.
- 🐛 **Fixed Column Mapping:** Improved sheet column detection (case-insensitive, space-friendly).

### 2026-01-21 - Quick Wins (Phase 1)
- ✅ Implemented bcrypt password hashing
- ✅ Added structured logging system
- ✅ Centralized configuration constants
- ✅ Input validation with Pydantic
- ✅ Migration guide created

### Previous Versions
See `docs/SYSTEM_OVERVIEW.md` for version history.

---

## 🤝 Contributing

### Before Making Changes
1. Read `docs/SYSTEM_OVERVIEW.md` for architecture
2. Check `docs/SYSTEM_ASSESSMENT.md` for planned improvements
3. Follow existing code structure

### Code Style
- Use type hints for all functions
- Log important actions (INFO/WARNING/ERROR)
- Extract magic numbers to `config.py`
- Validate inputs before processing

---

## 📞 Support

### Resources
- **Google Sheets:** [Link to actual sheet](https://docs.google.com/spreadsheets/d/1n1IPrJ9iPJyj74RDS7tPN8Jo8_iI2jVawbx8GKpHe78)
- **WordPress API:** Check `php/php.txt` for endpoints
- **Logs:** Check `logs/app.log` for detailed errors

### Common Issues
See `docs/MIGRATION_GUIDE.md` → Section 8

---

## 📜 License

Internal use only.

---

## 🎯 Roadmap

### Completed ✅
- Password hashing
- Structured logging
- Configuration constants
- Input validation

### Next Steps (Phase 2-6)
See `docs/SYSTEM_ASSESSMENT.md` for full plan:
- Unit tests (pytest)
- Type hints (mypy)
- Rate limiting
- Notification system
- Performance optimization

---

*Built with ❤️ for POD Automation*
