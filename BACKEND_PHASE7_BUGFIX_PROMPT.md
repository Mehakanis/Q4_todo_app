# Backend Phase 7: Fix Test Failures

Fix failing tests (35 failed, 29 errors). Call agents: `backend-testing`, `backend-feature-builder`.

## Critical Bugs:

### 1. Password Length Error (Most Tests)
**Error:** `ValueError: password cannot be longer than 72 bytes`
**Location:** `utils/password.py` bcrypt hashing
**Fix:** Truncate passwords to 72 bytes before hashing:
```python
def hash_password(password: str) -> str:
    password_bytes = password.encode('utf-8')[:72]  # Add truncation
    return pwd_context.hash(password_bytes.decode('utf-8'))
```

### 2. Task Service Unpacking Error
**Error:** `ValueError: too many values to unpack (expected 2)` at `task_service.py:131`
**Fix:** Check `get_tasks()` return value - should return `(tasks, metadata)` tuple

### 3. API Response Format
**Error:** Tests expect 201, getting 400; KeyError: 'success', 'data'
**Fix:** Verify response schemas match test expectations in `schemas/responses.py`

### 4. Email Validation
**Error:** `.startdot@example.com` passes validation (should fail)
**Fix:** Update `_validate_email()` in `services/auth_service.py` - reject emails starting with dot

### 5. CSV Import Exception
**Error:** Invalid CSV should raise HTTPException but doesn't
**Fix:** Add validation in `services/export_import_service.py` line ~340

## Run Tests:
```bash
cd phase-2/backend
uv run pytest tests/unit/ tests/api/ --tb=short -v
```

**Goal:** All tests passing, 80%+ coverage.

