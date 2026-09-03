# Database Migrations

Versioned SQL migrations for SmartMaintain.  Each file is named:

```
NNNN_short_description.sql
```

where `NNNN` is a zero-padded integer that determines execution order.

## How they run

The migration runner (`run_migrations.py`) is called once at container start
(before the service itself starts) and is safe to re-run — already-applied
migrations are skipped.

It maintains a `schema_migrations` table in PostgreSQL:

```sql
CREATE TABLE schema_migrations (
    version     TEXT PRIMARY KEY,
    applied_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
```

## Running manually

```bash
# From the project root (requires POSTGRES_URL in env)
python backend/migrations/run_migrations.py
```

## Adding a new migration

1. Create a new file: `backend/migrations/NNNN_my_change.sql`
2. Write idempotent SQL (use `IF NOT EXISTS`, `IF EXISTS`, etc.)
3. Commit the file — it will be applied automatically on next deploy
