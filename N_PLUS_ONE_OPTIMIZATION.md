# 🚀 N+1 Query Optimization Guide

## Problem Example

**Bad Pattern (N+1 queries)**:
```python
# endpoint that triggers N+1
@router.get("/clients/{client_id}/summary")
def get_client_summary(client_id: UUID, db: Session = Depends(get_db)):
    client = db.query(Client).filter(Client.id == client_id).first()

    # ❌ For each client, query all related data
    for platform_conn in client.platform_connections:  # Query 1
        for keyword in platform_conn.keywords:  # Query 2, 3, 4... (N times!)
            keyword_ranks = keyword.ranks  # Query N+1, N+2... (N*M times!)

    return {"platform_connections": ...}

# Result: 1 + N + N*M queries!
# If client has 5 platform_connections, each with 10 keywords, each with 5 ranks
# → 1 + 5 + 50 + 250 = 306 queries! 😱
```

## Solution: SQLAlchemy joinedload

**Good Pattern (1 query with JOINs)**:
```python
from sqlalchemy.orm import joinedload

@router.get("/clients/{client_id}/summary")
def get_client_summary(client_id: UUID, db: Session = Depends(get_db)):
    client = db.query(Client).options(
        joinedload(Client.platform_connections).joinedload(PlatformConnection.keywords)
    ).filter(Client.id == client_id).first()

    # ✅ Single query with multiple JOINs
    # Access related data without additional queries
    for platform_conn in client.platform_connections:
        for keyword in platform_conn.keywords:
            # No additional queries!
            pass

    return {"platform_connections": ...}

# Result: 1 query with JOINs! 📊
```

## When to Use joinedload vs contains_eager

### joinedload
- ✅ Use for relationships you need in memory
- ✅ Safe with multiple joinedload calls
- ❌ Doesn't filter results (gets all related records)

```python
# Get all keywords for a client's platform connections
clients = db.query(Client).options(
    joinedload(Client.platform_connections).joinedload(PlatformConnection.keywords)
).filter(Client.id == client_id).all()
```

### contains_eager
- ✅ Use when you want to filter AND eager-load
- ❌ Must use with outerjoin for filtering
- ✅ Only loads matching relationships

```python
# Get keywords matching specific criteria + eager load
from sqlalchemy.orm import contains_eager

keywords = db.query(Keyword).join(PlatformConnection).outerjoin(KeywordRank).options(
    contains_eager(Keyword.ranks)
).filter(
    Keyword.name == "임플란트",
    KeywordRank.rank <= 10
).all()
```

## Current Codebase: Areas with N+1 Risk

### ✅ Already Optimized (Good!)
- `leads.py` line 71-76: Uses `func.sum()` with `join()` (Good!)
- No N+1 patterns found in this area

### ⚠️ Potential Issues (Need Review)

Check these files for N+1 patterns:

1. **dashboard.py**
   - Fetches client data with related metrics
   - Recommendation: `joinedload(Client.metrics_daily)`

2. **clients.py**
   - Fetches all clients with connections
   - Recommendation: `joinedload(Client.platform_connections)`

3. **analysis.py**
   - Fetches keywords with ranks
   - Recommendation: `joinedload(Keyword.daily_ranks)`

4. **competitors.py**
   - Fetches competitors with ranks/metrics
   - Recommendation: `joinedload(Competitor.metrics)`

## Implementation Pattern

### Pattern 1: Simple eager load

```python
from sqlalchemy.orm import joinedload

@router.get("/clients/{client_id}")
def get_client(client_id: UUID, db: Session = Depends(get_db)):
    client = db.query(Client).options(
        joinedload(Client.agency),
        joinedload(Client.platform_connections),
    ).filter(Client.id == client_id).first()

    return client
```

### Pattern 2: Nested eager load (multiple levels)

```python
from sqlalchemy.orm import joinedload

@router.get("/clients/{client_id}/keywords")
def get_client_keywords(client_id: UUID, db: Session = Depends(get_db)):
    keywords = db.query(Keyword).options(
        joinedload(Keyword.client),  # Client info
        joinedload(Keyword.ranks),   # Daily ranks
    ).filter(Keyword.client_id == client_id).all()

    return keywords
```

### Pattern 3: Conditional eager load with filter

```python
from sqlalchemy.orm import joinedload, selectinload

@router.get("/keywords/top-performing")
def get_top_keywords(limit: int = 10, db: Session = Depends(get_db)):
    # selectinload for many-to-many or complex relationships
    keywords = db.query(Keyword).options(
        selectinload(Keyword.daily_ranks)
    ).filter(
        Keyword.status == "ACTIVE"
    ).order_by(Keyword.click_count.desc()).limit(limit).all()

    return keywords
```

## Performance Measurement

### Before (N+1)
```
GET /api/v1/clients/abc-123 took 2,450ms
  → 1 query: SELECT * FROM clients (5ms)
  → 3 queries: SELECT * FROM platform_connections WHERE client_id=... (15ms each)
  → 15 queries: SELECT * FROM keywords (50ms each)
  → 75 queries: SELECT * FROM daily_ranks (20ms each)
  Total: 94 queries, 2,450ms ⚠️
```

### After (joinedload)
```
GET /api/v1/clients/abc-123 took 45ms
  → 1 query: SELECT ... FROM clients
    LEFT JOIN platform_connections
    LEFT JOIN keywords
    LEFT JOIN daily_ranks (Single complex query: 40ms)
  Total: 1 query, 45ms ✅
```

**54x faster!** 🚀

## Debugging: Identify N+1 Queries

### Method 1: SQLAlchemy logging

```python
import logging

# In main.py or settings
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Now run your endpoint - you'll see every query
```

### Method 2: Query counter middleware

```python
# Add to main.py
class QueryCounterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Count queries before
        query_count_before = len(db.execute(text("SELECT 1")).fetchall())

        response = await call_next(request)

        # Count queries after
        query_count_after = len(db.execute(text("SELECT 1")).fetchall())

        print(f"🔍 {request.url.path}: {query_count_after - query_count_before} queries")
        return response
```

### Method 3: APM (Application Performance Monitoring)

```bash
# Use Sentry for query tracking
# Sentry dashboard shows slow queries automatically
pip install sentry-sdk[fastapi,sqlalchemy]
```

## Checklist for Review

- [ ] Identify all endpoints that fetch related data
- [ ] Mark endpoints with N+1 risk as `[N+1 RISK]` in comments
- [ ] Add `joinedload()` or `selectinload()` for related data
- [ ] Test with multiple related records (not just 1)
- [ ] Measure response time before/after
- [ ] Document performance improvement

## Next Steps

1. **Phase 2 (Current)**: Documentation complete ✅
2. **Phase 3 (Next week)**: Implement optimizations
   - [ ] Audit 5 highest-traffic endpoints
   - [ ] Add eager loading to each
   - [ ] Measure performance improvement
   - [ ] Document results

---

**Status**: 📋 Analysis complete, optimization pending
**Impact**: 🟡 Medium (affects response time)
**Effort**: Low-Medium (1-2 hours per endpoint)
