# 🎯 API Error Response Standardization

## Problem: Inconsistent Error Formats

**Current state** - each endpoint returns different error formats:

```python
# ❌ status.py
return {"status": "ERROR", "message": str(e)}

# ❌ leads.py
raise HTTPException(status_code=404, detail="Lead not found")

# ❌ clients.py
return {"status": "error", "detail": "..."}

# ❌ auth.py
raise HTTPException(status_code=401, detail="Could not validate credentials")
```

**Frontend Problem**:
```typescript
// Frontend must handle multiple error formats
try {
    const response = await api.post('/leads/', data);
} catch (error: any) {
    // ❓ Which format is it?
    const msg =
        error?.response?.data?.detail ||  // HTTPException
        error?.response?.data?.message || // status.py
        error?.response?.data?.error ||   // clients.py
        'Unknown error';
}
```

## Solution: Standard Error Response Format

### Standard Format (RFC 7807 - Problem Details)

```python
# Universal error response format
{
    "error": {
        "code": "INVALID_INPUT",           # Machine-readable code
        "message": "User-friendly message", # Human-readable
        "detail": "Additional context",    # Optional details
        "path": "/api/v1/leads"            # Request path
    },
    "timestamp": "2026-02-20T12:34:56Z",   # When error occurred
    "request_id": "abc-123-def"             # For debugging
}
```

### Standard HTTP Status Codes

| Code | Meaning | When to use |
|------|---------|------------|
| 400 | Bad Request | Invalid input, validation failure |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Valid token but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate request, race condition |
| 422 | Unprocessable Entity | Validation error with details |
| 500 | Internal Server Error | Unexpected error |
| 503 | Service Unavailable | Database/external service down |

## Implementation

### Step 1: Create ErrorResponse Schema

```python
# backend/app/core/errors.py (NEW FILE)

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: Dict[str, Any] = {
        "code": str,      # e.g., "INVALID_INPUT", "NOT_FOUND"
        "message": str,   # e.g., "리드를 찾을 수 없습니다"
        "detail": Optional[str],  # Additional context
    }
    timestamp: datetime
    request_id: str

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "LEAD_NOT_FOUND",
                    "message": "요청한 리드를 찾을 수 없습니다.",
                    "detail": "ID: 123abc"
                },
                "timestamp": "2026-02-20T12:34:56Z",
                "request_id": "req-uuid-1234"
            }
        }
```

### Step 2: Create Error Codes (Enum)

```python
# backend/app/core/errors.py (continue)

from enum import Enum

class ErrorCode(str, Enum):
    """Standard error codes"""
    # Authentication
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Validation
    INVALID_INPUT = "INVALID_INPUT"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # Resources
    NOT_FOUND = "NOT_FOUND"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"

    # Business Logic
    INVALID_STATE = "INVALID_STATE"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    CONFLICT = "CONFLICT"

    # System
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    DATABASE_ERROR = "DATABASE_ERROR"
```

### Step 3: Create Standardized Exception

```python
# backend/app/core/errors.py (continue)

from fastapi import HTTPException
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class APIException(HTTPException):
    """Standardized API exception"""

    def __init__(
        self,
        status_code: int,
        error_code: str,
        message: str,
        detail: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.error_code = error_code
        self.message = message
        self.detail = detail
        self.request_id = request_id or str(uuid4())
        self.timestamp = datetime.utcnow().isoformat() + "Z"

        # Build error response
        error_detail = {
            "code": error_code,
            "message": message,
        }
        if detail:
            error_detail["detail"] = detail

        super().__init__(
            status_code=status_code,
            detail={
                "error": error_detail,
                "timestamp": self.timestamp,
                "request_id": self.request_id,
            }
        )

        # Log error
        logger.warning(
            f"API Error [{self.request_id}] {status_code} {error_code}: {message}",
            extra={"error_code": error_code, "request_id": self.request_id}
        )
```

### Step 4: Global Exception Handler

```python
# backend/app/main.py (add this)

from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.errors import APIException, ErrorCode
import logging

logger = logging.getLogger(__name__)

@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    """Handle APIException with standard format"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standard format"""
    request_id = str(uuid4())
    logger.error(
        f"Unexpected error [{request_id}]: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id}
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": ErrorCode.INTERNAL_ERROR,
                "message": "서버에서 예기치 않은 오류가 발생했습니다.",
                "detail": "관리자에게 문의하세요." if not DEBUG else str(exc),
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
        }
    )
```

### Step 5: Update Endpoints to Use Standard Errors

```python
# BEFORE ❌
@router.get("/{lead_id}")
def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead

# AFTER ✅
from app.core.errors import APIException, ErrorCode

@router.get("/{lead_id}")
def get_lead(lead_id: UUID, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise APIException(
            status_code=404,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            message=f"리드를 찾을 수 없습니다.",
            detail=f"ID: {lead_id}"
        )
    return lead
```

## Frontend Usage

### Before (multiple error formats)
```typescript
// ❌ Fragile - breaks if backend changes format
try {
    await api.post('/leads/', data);
} catch (error: any) {
    const msg =
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        'Unknown error';
    toast.error(msg);
}
```

### After (standardized format)
```typescript
// ✅ Robust - works with any error
interface ErrorResponse {
    error: {
        code: string;
        message: string;
        detail?: string;
    };
    timestamp: string;
    request_id: string;
}

try {
    await api.post('/leads/', data);
} catch (error: any) {
    const data = error?.response?.data as ErrorResponse;

    // Always access same path
    const message = data?.error?.message || 'Unknown error';
    const code = data?.error?.code;
    const requestId = data?.request_id;

    // Can react based on error code
    if (code === 'DUPLICATE_RESOURCE') {
        toast.error('이미 등록된 리드입니다.');
    } else if (code === 'INSUFFICIENT_PERMISSIONS') {
        toast.error('권한이 없습니다.');
    } else {
        toast.error(message);
    }

    // Log for debugging
    console.log(`Error [${requestId}]: ${code} - ${message}`);
}
```

## Migration Path

### Phase 1: Setup (Today)
- [ ] Create `app/core/errors.py` with ErrorResponse, ErrorCode, APIException
- [ ] Add exception handlers to main.py
- [ ] Document standard format

### Phase 2: Migrate (This week)
- [ ] Update `auth.py` to use APIException
- [ ] Update `leads.py` to use APIException
- [ ] Update `clients.py` to use APIException
- [ ] Update `users.py` to use APIException

### Phase 3: Frontend (Next week)
- [ ] Update error handling in `api.ts`
- [ ] Test error scenarios
- [ ] Update error toast messages

## Benefits

| Aspect | Before | After |
|--------|--------|-------|
| **Consistency** | ❌ Different per endpoint | ✅ Same everywhere |
| **Debugging** | ❌ Missing request IDs | ✅ Every error tracked |
| **Frontend** | ❌ Multiple error formats to handle | ✅ One standard format |
| **API Docs** | ❌ Unclear | ✅ Clear error codes |
| **Support** | ❌ Hard to trace | ✅ Easy (request_id) |

## Example Error Responses

### 404 Not Found
```json
{
    "error": {
        "code": "RESOURCE_NOT_FOUND",
        "message": "리드를 찾을 수 없습니다.",
        "detail": "ID: 550e8400-e29b-41d4-a716-446655440000"
    },
    "timestamp": "2026-02-20T12:34:56Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### 422 Validation Error
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "입력 데이터가 유효하지 않습니다.",
        "detail": "필수 필드: name, email"
    },
    "timestamp": "2026-02-20T12:34:56Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

### 401 Unauthorized
```json
{
    "error": {
        "code": "INVALID_CREDENTIALS",
        "message": "이메일 또는 비밀번호가 올바르지 않습니다.",
        "detail": null
    },
    "timestamp": "2026-02-20T12:34:56Z",
    "request_id": "550e8400-e29b-41d4-a716-446655440003"
}
```

---

**Status**: 📋 Specification complete
**Impact**: 🟡 Medium (developer experience)
**Effort**: Medium (3-4 hours for full migration)
**Timeline**: Phase 2-3
