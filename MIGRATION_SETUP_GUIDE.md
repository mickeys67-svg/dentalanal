# 🔧 Database Migration Setup Guide (Alembic)

## Problem
현재 `main.py`의 `startup` 작업에서 자동으로 스키마 변경을 감지하고 ALTER TABLE을 실행:
- ❌ 동시성 문제 (여러 서버가 동시에 ALTER TABLE 시도)
- ❌ 마이그레이션 기록이 없음
- ❌ 롤백 불가능
- ❌ 프로덕션에서 위험한 schema drift

## Solution: Alembic Integration

### 1️⃣ Installation

```bash
cd backend
pip install alembic
```

### 2️⃣ Initialize Alembic

```bash
alembic init alembic
```

This creates:
```
backend/
├── alembic/
│   ├── versions/          # Migration scripts go here
│   ├── env.py            # Alembic environment config
│   └── script.py.mako    # Template for new migrations
├── alembic.ini           # Alembic configuration
└── ...
```

### 3️⃣ Configure alembic.ini

Edit `backend/alembic.ini`:

```ini
[alembic]
# ... existing config ...

sqlalchemy.url = driver://user:password@localhost/dbname
# COMMENT THIS OUT - we'll use settings instead

[loggers]
keys = root,sqlalchemy,alembic

level = WARN
```

### 4️⃣ Configure env.py

Edit `backend/alembic/env.py`:

```python
from app.core.config import settings
from app.core.database import engine
from app.models.models import Base

# Get DATABASE_URL from settings
config.set_main_option(
    "sqlalchemy.url",
    settings.get_database_url()
)

# Target metadata for autogenerate
target_metadata = Base.metadata

def run_migrations_online() -> None:
    # Use engine from app.core.database
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        # ... rest of config
```

### 5️⃣ Create Initial Migration

```bash
cd backend
alembic revision --autogenerate -m "Initial schema"
```

This creates a migration file like:
```
alembic/versions/001_initial_schema.py
```

### 6️⃣ Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade 001_initial_schema

# Rollback last migration
alembic downgrade -1

# Check current version
alembic current
```

### 7️⃣ Create New Migrations

After modifying `models.py`:

```bash
# Auto-detect changes and create migration script
alembic revision --autogenerate -m "Add user_profile column"

# Review the generated migration file
cat alembic/versions/002_add_user_profile_column.py

# Apply it
alembic upgrade head
```

### 8️⃣ Update Startup Logic

Remove the auto-migration code from `main.py`:

```python
# DELETE THIS BLOCK from main.py
try:
    from sqlalchemy import text
    with engine.connect() as conn:
        # This auto-ALTER TABLE logic should be removed
        # Schema changes now happen via alembic migrations
        ...
except Exception as e:
    logger.error(...)
```

Add Alembic runner instead:

```python
# In main.py startup
async def run_startup_tasks():
    from alembic.config import Config
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from alembic.operations import Operations

    # Apply pending migrations
    alembic_cfg = Config("alembic.ini")
    engine = create_engine(settings.get_database_url())

    with engine.begin() as connection:
        ctx = MigrationContext.configure(connection)
        op = Operations(ctx)
        # Auto-upgrade to head
        alembic_cfg.set_main_option(
            "sqlalchemy.url",
            settings.get_database_url()
        )
```

## Benefits of Alembic

| Feature | Before (Auto) | After (Alembic) |
|---------|--------------|-----------------|
| Migration tracking | ❌ None | ✅ Version control |
| Rollback | ❌ Impossible | ✅ `alembic downgrade -1` |
| Multi-server safety | ❌ Race condition | ✅ Database lock prevents conflicts |
| Schema review | ❌ Auto executed | ✅ Review before running |
| Production safety | ❌ High risk | ✅ Test in staging first |

## Deployment Flow

```
GitHub Actions
├── 1. Build backend
├── 2. Connect to database
├── 3. Run: alembic upgrade head
│   └── Applies all pending migrations
├── 4. Deploy to Cloud Run
│   └── No more startup schema drift!
└── 5. Health check passes
```

## Emergency: Rollback

If something goes wrong:

```bash
# Check what version you're at
alembic current

# List all migration versions
alembic history

# Downgrade to previous version
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision_hash>
```

## Next Steps

1. ✅ Commit current state
2. ⏳ Phase 3 (next week): Implement Alembic integration
3. ⏳ Phase 4: Migrate all manual migrations to Alembic scripts

---

**Status**: 📋 Planning (Not yet implemented)
**Impact**: 🔴 Critical for production safety
**Effort**: Medium (1-2 hours setup)
**Timeline**: Phase 3 (Next week)
