# 🚀 Antigravity AI - Best Practices cho POD Automation System
> **Version:** 1.0  
> **Last Updated:** 2026-01-21  
> **Purpose:** Hướng dẫn tối ưu hóa giao tiếp với Antigravity AI để đạt hiệu suất cao nhất

---

## 🎯 Mục tiêu

- **Zero-latency:** Phản hồi nhanh nhất có thể
- **Token-efficiency:** Tiết kiệm token input/output
- **High-quality code:** Code chính xác, maintainable

---

## ⚙️ 1. Cấu hình Model (Recommended Settings)

### Temperature & Sampling
```yaml
Temperature: 0.1 - 0.2   # Low creativity, high precision
Top P: 0.8               # Focused vocabulary
Max Tokens: 2048         # Prevent overly verbose responses
```

**Rationale:**
- Code generation cần deterministic, không cần "creativity"
- Temperature thấp → Ít hallucination, câu trả lời chính xác hơn

---

## 📝 2. System Instruction Template

Sử dụng system prompt này khi khởi tạo:

```
Bạn là Antigravity, công cụ coding assistant chuyên nghiệp.

QUY TẮC HOẠT ĐỘNG:
1. **Concise:** Trả lời ngắn gọn, tránh giải thích dài dòng
2. **Code-first:** Ưu tiên code block, giải thích chỉ khi cần
3. **Smart comments:** Comment khi logic phức tạp, bỏ qua điều hiển nhiên
4. **DRY principle:** Không lặp lại code cũ, chỉ hiển thị phần thay đổi
5. **Context-aware:** Đọc kỹ file trước khi edit, respect existing patterns

Đối với POD Automation System:
- Tuân thủ Config class cho constants
- Sử dụng logger thay vì print()
- Validate input với pydantic models
- Add type hints cho tất cả functions
```

---

## ⚡ 3. Kỹ thuật Prompting Hiệu quả

### ✅ DO: Diff-Context (Recommended)
```
"Sửa lỗi bcrypt trong function check_admin_login():
[paste only relevant function]
Error: Invalid salt
```

**Lợi ích:** 
- Tiết kiệm ~80% tokens
- Context rõ ràng
- Phản hồi nhanh hơn

### ❌ DON'T: Full File Paste
```
"Sửa lỗi trong file này:
[paste entire 500-line file]
```

**Tại sao tệ:**
- Lãng phí tokens
- Model dễ bị distracted
- Chậm hơn 3-5x

---

## 🛠️ 4. Tool Usage Strategy

### Ưu tiên dùng Tools thay vì Generate

**Tốt:**
```python
view_file("db.py", start=70, end=85)  # View specific function
replace_file_content(...)              # Edit surgically
```

**Tệ:**
```python
"Hãy viết lại toàn bộ file db.py cho tôi"  # Regenerate everything
```

**Lý do:** 
- Tool calls KHÔNG tốn output tokens
- Chính xác hơn (no copy-paste errors)
- Faster execution

---

## 🏎️ 5. Batch Operations (Tiết kiệm API Calls)

### ✅ Nhóm requests liên quan

**Tốt:**
```
"Cần update 3 files:
1. woo.py: Thay Config.MAX_RETRIES
2. importer.py: Thay Config.CHUNK_SIZE  
3. deleter.py: Thay Config.BATCH_SIZE
```

**Tệ:**
```
[3 messages riêng lẻ cho mỗi file]
```

**Tiết kiệm:** ~60% API calls + context switching

---

## 📊 6. Project-Specific Best Practices

### POD Automation System Patterns

#### 6.1. Config Constants
```python
# ✅ DO
from config import Config
time.sleep(Config.RETRY_DELAY)

# ❌ DON'T
time.sleep(2)  # Magic number
```

#### 6.2. Logging
```python
# ✅ DO
from src.utils.logger import logger
logger.info(f"Import started")

# ❌ DON'T
print(f"Import started")
```

#### 6.3. Validation
```python
# ✅ DO
is_valid, error, validated = validate_product_data(data)
if not is_valid:
    logger.error(f"Validation failed: {error}")

# ❌ DON'T
# No validation, trust input
```

#### 6.4. Type Hints
```python
# ✅ DO
def get_val(row: Dict[str, Any], keys: List[str]) -> str:
    ...

# ❌ DON'T
def get_val(row, keys):  # No hints
    ...
```

---

## 🧪 7. Example Interactions

### Scenario 1: Add New Feature
**User:**
```
Thêm rate limiting cho login function
```

**Antigravity (Optimal):**
```python
# src/repositories/db.py
from functools import wraps
import time

_login_attempts = {}

def rate_limit(max_calls=5, period=60):
    def decorator(func):
        @wraps(func)
        def wrapper(username, *args, **kwargs):
            now = time.time()
            key = username
            if key not in _login_attempts:
                _login_attempts[key] = []
            
            # Clean old attempts
            _login_attempts[key] = [t for t in _login_attempts[key] if now - t < period]
            
            if len(_login_attempts[key]) >= max_calls:
                logger.warning(f"Rate limit exceeded for {username}")
                return False
            
            _login_attempts[key].append(now)
            return func(username, *args, **kwargs)
        return wrapper
    return decorator

@rate_limit(max_calls=5, period=60)
def check_admin_login(username: str, password: str) -> bool:
    # ... existing code
```

**Note:** Chỉ trả code, không nói "Đây là code của bạn" hay giải thích dài dòng.

---

### Scenario 2: Debug Issue
**User:**
```
Login fail với error: "Bcrypt error: Invalid salt"
Current code: [paste function]
```

**Antigravity (Optimal):**
```
Issue: password_hash is NULL or malformed

Fix:
```python
# Add null check before bcrypt
if user_data.get('password_hash'):
    try:
        # Verify hash format
        if not user_data['password_hash'].startswith('$2b$'):
            logger.error(f"Invalid hash format for {username}")
            return False
        
        is_valid = bcrypt.checkpw(...)
```

Check:
1. Run migration: `ALTER TABLE admin_users ADD COLUMN password_hash TEXT`
2. Generate hash: `python generate_password_hash.py`
3. Update DB
```

---

## 📈 8. Performance Metrics

### Expected Improvements

| Metric | Before | After (w/ Best Practices) |
|--------|--------|---------------------------|
| Avg Response Time | 8-12s | 3-5s |
| Tokens/Request | 3000-5000 | 800-1500 |
| Accuracy | ~85% | ~95% |
| Follow-ups Needed | 30% | <10% |

---

## ✅ 9. Checklist cho Mỗi Request

Trước khi gửi prompt, tự hỏi:

- [ ] Tôi đã view file cần thiết chưa? (Dùng `view_file`)
- [ ] Tôi có thể narrow down context không? (Chỉ paste function cần thiết)
- [ ] Tôi có thể batch nhiều yêu cầu nhỏ không?
- [ ] Request của tôi rõ ràng chưa? (Avoid "sửa lỗi này" mà không specify)
- [ ] Tôi đã cung cấp error message/logs chưa?

---

## 🚫 10. Common Anti-Patterns (Tránh)

### 10.1. Vague Requests
```
❌ "Code này có vẻ sai"
✅ "Function import_batch() raise IndexError tại line 45 khi list rỗng"
```

### 10.2. Asking for Full Rewrites
```
❌ "Viết lại toàn bộ importer.py"
✅ "Refactor worker_import_batch() để dùng Config constants"
```

### 10.3. No Context
```
❌ "Sửa bug này: [paste error only]"
✅ "Error khi import: [error] - Code hiện tại: [paste function]"
```

---

## 🎓 11. Advanced Tips

### 11.1. Use Markdown Formatting
Format code với backticks để AI parse dễ hơn:
```
Function cần fix: `check_admin_login()` trong file `db.py`
```

### 11.2. Specify Priority
```
CRITICAL: Password hashing broken - users can't login
Medium: Add type hints to utils/common.py
Low: Refactor CSS styles
```

### 11.3. Reference Existing Patterns
```
"Thêm logging tương tự như trong importer.py:
logger.info(f'Starting import for {site_name}')
"
```

---

## 📚 12. Related Documentation

- [System Overview](SYSTEM_OVERVIEW.md) - Hiểu kiến trúc hệ thống
- [Migration Guide](MIGRATION_GUIDE.md) - Hướng dẫn database migration
- [System Assessment](SYSTEM_ASSESSMENT.md) - Roadmap cải tiến

---

## 🔄 13. Feedback Loop

Sau mỗi interaction, đánh giá:

**Tốt:**
- Response nhanh (<5s)
- Code chính xác ngay lần đầu
- Không cần clarification

**Cần cải thiện:**
- Phải hỏi lại nhiều lần
- Code có bugs
- Response quá dài/ngắn

→ Adjust prompt tiếp theo

---

## 🛡️ 14. Giao thức "Fail-Safe" (Xử lý Lỗi & Tắc nghẽn)

### 14.1. Quy tắc "Fail Fast"
**System Instruction bổ sung:**
```
Nếu tác vụ (đọc file, search, phân tích) thất bại hoặc tốn quá nhiều thời gian:
1. KHÔNG xin lỗi hay giải thích dài dòng
2. KHÔNG tự ý retry quá 1 lần
3. TRẢ VỀ NGAY mã lỗi chuẩn
```

### 14.2. Mã lỗi chuẩn (Standard Error Tokens)

| Sự cố | Error Token | Hành động Client |
|-------|-------------|------------------|
| Yêu cầu mơ hồ | `>>AMBIGUOUS<<` | Hỏi lại rõ hơn |
| Load file/link fail | `>>LOAD_FAIL<<` | Bypass hoặc nhập trực tiếp |
| Vượt khả năng | `>>CAP_LIMIT<<` | Break thành smaller tasks |
| Bị kẹt logic/loop | `>>STUCK<<` | Reset context |
| Thiếu thông tin | `>>MISSING: [info]<<` | Request clarification |

**Example Usage:**
```python
# Client code
response = antigravity.generate(prompt)
if ">>AMBIGUOUS<<" in response:
    prompt = get_clarification_from_user()
    response = antigravity.generate(prompt)
```

### 14.3. Xử lý thiếu context
```
System Rule: "Nếu thiếu biến số hoặc context để viết code chính xác:
KHÔNG đoán. Trả về: >>MISSING: [tên thông tin]<<"
```

**Example:**
```
User: "Thêm validation cho field X"
AI: ">>MISSING: X field type and constraints<<"
```

---

## ⏱️ 15. Kỹ thuật chống "Treo" (Anti-Hanging Strategy)

### 15.1. Cắt ngắn quy trình suy nghĩ
**System Prompt Enhancement:**
```
⚡ PERFORMANCE MODE:
- Skip verbose reasoning
- Go straight to solution code
- No explanations unless critical
- Max 3 sentences for non-code responses
```

### 15.2. Timeout Configuration (Client-side)

**Python Example:**
```python
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure timeouts
session = requests.Session()
retry_strategy = Retry(
    total=2,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)

# Set timeouts
CONNECT_TIMEOUT = 5   # 5s to connect
READ_TIMEOUT = 30     # 30s for response
TOTAL_TIMEOUT = 35

try:
    response = session.post(
        ANTIGRAVITY_API_URL,
        json=payload,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
    )
except requests.Timeout:
    # Fallback: Retry with simpler prompt
    simplified_prompt = simplify_request(original_prompt)
    response = session.post(API_URL, json={'prompt': simplified_prompt})
```

### 15.3. Progressive Timeout Strategy
```
Attempt 1: Full complex prompt (30s timeout)
  ↓ FAIL
Attempt 2: Simplified prompt (20s timeout)
  ↓ FAIL  
Attempt 3: Minimal prompt (10s timeout)
  ↓ FAIL
Fallback: Manual intervention
```

---

## 🔄 16. Circuit Breaker Pattern

Tự động dừng nếu Model fail liên tục (production best practice):

```python
class AntigravityCircuitBreaker:
    def __init__(self, failure_threshold=3, timeout=60):
        self.failures = 0
        self.threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                return ">>CIRCUIT_BREAK<<Circuit breaker is OPEN. Try again later."
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.threshold:
                self.state = "OPEN"
                logger.error(f"Circuit breaker opened after {self.failures} failures")
            
            raise

# Usage
breaker = AntigravityCircuitBreaker(failure_threshold=3, timeout=60)
response = breaker.call(antigravity_api.generate, prompt)
```

---

## 📊 17. Context Window Management

Monitor token usage để tránh overflow:

### 17.1. Token Budget Tracking
```python
from config import Config

class TokenBudget:
    def __init__(self):
        self.used = 0
        self.limit = Config.MAX_CONTEXT_TOKENS  # 32k for Gemini
    
    def add(self, tokens):
        self.used += tokens
        utilization = (self.used / self.limit) * 100
        
        if utilization > 95:
            logger.critical(f"Token usage at {utilization:.1f}% - CLEAR CONTEXT!")
            return ">>CTX_OVERFLOW<<"
        elif utilization > 90:
            logger.warning(f"Token usage at {utilization:.1f}% - Consider summarizing")
            return ">>CTX_WARNING<<"
        elif utilization > 80:
            logger.info(f"Token usage at {utilization:.1f}%")
        
        return "OK"
```

### 17.2. Auto-Summarization Strategy
```
At 80% capacity:
  → Summarize conversation history
  → Keep only last 5 messages + context

At 90% capacity:
  → Aggressive summarization
  → Keep only current task context

At 95% capacity:
  → Clear and restart
  → Save summary to file for reference
```

### 17.3. Smart Context Pruning
```python
def prune_context(messages, max_tokens=8000):
    """
    Keep important messages, summarize old ones.
    Priority: System > Latest User > Latest AI > Older messages
    """
    system_msg = messages[0]  # Always keep
    recent = messages[-3:]     # Keep last 3
    
    # Summarize middle messages
    middle = messages[1:-3]
    summary = f"[Previous context: {len(middle)} messages about {extract_topics(middle)}]"
    
    return [system_msg, summary] + recent
```

---

## 🎮 18. Progressive Degradation (Graceful Fallback)

Khi request phức tạp fail, tự động đơn giản hóa:

### 18.1. Complexity Levels
```python
COMPLEXITY_LEVELS = {
    "EXPERT": {
        "temperature": 0.1,
        "max_tokens": 2048,
        "tools": ["view_file", "edit_file", "search_codebase"]
    },
    "STANDARD": {
        "temperature": 0.2,
        "max_tokens": 1024,
        "tools": ["view_file", "edit_file"]
    },
    "SIMPLE": {
        "temperature": 0.3,
        "max_tokens": 512,
        "tools": ["view_file"]
    },
    "MINIMAL": {
        "temperature": 0.4,
        "max_tokens": 256,
        "tools": []
    }
}
```

### 18.2. Auto-Degradation Flow
```
Request: "Refactor entire codebase with new architecture"
  ↓ Try EXPERT mode → TIMEOUT
Degrade to STANDARD: "Refactor main modules"
  ↓ Try STANDARD → PARTIAL SUCCESS
Keep at STANDARD for next request
```

### 18.3. Recovery Strategy
```python
def execute_with_degradation(prompt, start_level="EXPERT"):
    levels = ["EXPERT", "STANDARD", "SIMPLE", "MINIMAL"]
    current_idx = levels.index(start_level)
    
    while current_idx < len(levels):
        level = levels[current_idx]
        config = COMPLEXITY_LEVELS[level]
        
        try:
            response = antigravity.generate(
                prompt, 
                **config,
                timeout=30
            )
            logger.info(f"Success at {level} level")
            return response
        except TimeoutError:
            logger.warning(f"{level} timed out, degrading...")
            current_idx += 1
    
    # All levels failed
    return ">>ALL_LEVELS_FAILED<< Please manually review the request"
```

---

## 🚨 19. Production Monitoring & Alerts

### 19.1. Health Metrics
```python
# Track key metrics
metrics = {
    "avg_response_time": [],
    "timeout_rate": 0,
    "error_rate": 0,
    "token_efficiency": []  # output_tokens / input_tokens
}

def log_metrics(response, duration):
    metrics["avg_response_time"].append(duration)
    
    # Alert if degrading
    if len(metrics["avg_response_time"]) > 10:
        avg = sum(metrics["avg_response_time"][-10:]) / 10
        if avg > 15:  # 15s average
            logger.warning(f"⚠️ Avg response time: {avg:.1f}s - degrading!")
```

### 19.2. Alert Thresholds
```python
ALERT_THRESHOLDS = {
    "response_time": 20,      # seconds
    "timeout_rate": 0.10,     # 10%
    "error_rate": 0.05,       # 5%
    "token_efficiency": 0.5   # output/input ratio
}

if metrics["timeout_rate"] > ALERT_THRESHOLDS["timeout_rate"]:
    send_alert("High timeout rate detected!")
```

---

## ✅ 20. Complete Production Checklist

Before deploying Antigravity integration:

- [ ] **Timeouts configured** (5s connect, 30s read)
- [ ] **Circuit breaker implemented** (3 failures → open)
- [ ] **Error tokens standardized** (`>>ERROR_TYPE<<`)
- [ ] **Context window monitored** (alert at 80%)
- [ ] **Degradation levels defined** (4 complexity tiers)
- [ ] **Logging configured** (`logs/antigravity.log`)
- [ ] **Metrics tracked** (response time, error rate)
- [ ] **Fallback strategy** (manual intervention path)
- [ ] **Rate limiting** (respect API quotas)
- [ ] **Retry logic** (exponential backoff)

---

*Document này sẽ được update dựa trên real-world usage patterns.*
