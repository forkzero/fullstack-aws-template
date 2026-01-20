# Authentication Hardening Plan

Prioritized security fixes for the authentication implementation.

---

## P0: Critical Security (Before Production)

### 1. Fix Race Condition in User Creation
**Risk**: Duplicate users, integrity errors
**File**: `backend/app/core/auth.py`

Use database-level upsert to handle concurrent requests safely.

### 2. Validate Token Type
**Risk**: Wrong token type accepted
**File**: `backend/app/core/auth.py`

```python
if claims.get("token_use") != "access":
    raise HTTPException(status_code=401, detail="Invalid token type")
```

### 3. Add Pagination Limits
**Risk**: DoS via resource exhaustion
**Files**: API endpoints

```python
MAX_PAGE_SIZE = 100
page_size: int = Query(20, ge=1, le=MAX_PAGE_SIZE)
```

### 4. Sanitize Error Messages
**Risk**: Information leakage
**File**: `backend/app/core/auth.py`

Log full errors internally, return generic messages to clients.

### 5. Add Database Indexes
**Risk**: Performance degradation
**File**: Migration

```python
op.create_index('ix_resources_user_id', 'resources', ['user_id'])
op.create_index('ix_resources_organization_id', 'resources', ['organization_id'])
```

---

## P1: High Priority (Before Beta)

### 6. Thread-Safe JWKS Cache
**Risk**: Cache corruption under load
**File**: `backend/app/core/auth.py`

Use asyncio.Lock or Redis for cross-worker cache.

### 7. WebSocket Token Refresh
**Risk**: Long sessions fail mid-operation
**File**: WebSocket handlers

Add periodic token validation during long-running operations.

### 8. Auth Integration Tests
**Risk**: Auth logic untested
**File**: New test file

```python
def test_expired_token_rejected():
def test_wrong_audience_rejected():
def test_malformed_token_rejected():
```

---

## P2: Medium Priority (Before GA)

### 9. Role-Based Access Control
```python
def require_role(allowed_roles: list[str]):
    def checker(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return checker
```

### 10. Soft Delete
```python
class SoftDeleteMixin:
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(UUID, nullable=True)
```

### 11. Audit Trail
```python
class AuditLog(Base):
    user_id = Column(UUID)
    action = Column(String)  # create, update, delete
    resource_type = Column(String)
    resource_id = Column(UUID)
    changes = Column(JSONB)
```

---

## P3: Nice to Have (Post-Launch)

- MFA support via Cognito
- Token revocation with Redis blacklist
- Abstract auth provider interface
- Feature flags for auth settings

---

## Testing Checklist

- [ ] Unit test for each fix
- [ ] Integration test with mocked Cognito
- [ ] Manual test in preprod
- [ ] Security scan (OWASP ZAP)

## Monitoring

1. Auth failure rate (alert if > 5%)
2. User creation rate (detect race conditions)
3. Token validation latency
4. 401/403 response rate by endpoint
