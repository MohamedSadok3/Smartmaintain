"""
Migration runner for SmartMaintain.

Usage:
    python backend/migrations/run_migrations.py

Reads all *.sql files from the same directory in lexicographic order,
skips files that have already been applied, and records each successful
migration in the `schema_migrations` table.

Safe to run multiple times (idempotent).
"""

import logging
import os
import sys
from pathlib import Path

import psycopg2
import bcrypt
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [migrations] %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent

CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     TEXT PRIMARY KEY,
    applied_at  TIMESTAMP NOT NULL DEFAULT NOW()
);
"""

SELECT_APPLIED = "SELECT version FROM schema_migrations ORDER BY version;"

INSERT_APPLIED = "INSERT INTO schema_migrations (version) VALUES (%s);"


def bootstrap_superadmin(conn) -> None:
    """Create or rotate the bootstrap superadmin from environment values."""
    email = os.environ.get("SUPERADMIN_EMAIL", "superadmin@smartmaintain.local").strip().lower()
    password = os.environ.get("SUPERADMIN_PASSWORD")
    if not password or len(password) < 12:
        raise RuntimeError("SUPERADMIN_PASSWORD must contain at least 12 characters.")
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (name, email, password_hash, role, plant_id, machines)
            VALUES ('Super Admin', %s, %s, 'superadmin', NULL, '{}')
            ON CONFLICT (email) DO UPDATE
            SET password_hash = EXCLUDED.password_hash,
                role = 'superadmin';
            """,
            (email, password_hash),
        )
    conn.commit()


def get_connection():
    url = os.environ.get("POSTGRES_URL")
    if not url:
        logger.error("POSTGRES_URL environment variable is not set.")
        sys.exit(1)
    return psycopg2.connect(url)


def get_migration_files() -> list[Path]:
    """Return all .sql files in the migrations directory, sorted."""
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    return files


def run_migrations() -> None:
    conn = get_connection()
    conn.autocommit = False

    try:
        with conn.cursor() as cur:
            # Ensure the tracking table exists
            cur.execute(CREATE_MIGRATIONS_TABLE)
            conn.commit()

            # Fetch already-applied versions
            cur.execute(SELECT_APPLIED)
            applied = {row[0] for row in cur.fetchall()}

        migration_files = get_migration_files()

        if not migration_files:
            logger.info("No migration files found in %s.", MIGRATIONS_DIR)
            return

        applied_count = 0
        skipped_count = 0

        for filepath in migration_files:
            version = filepath.name  # e.g. "0001_initial_schema.sql"

            if version in applied:
                logger.debug("Skipping already-applied migration: %s", version)
                skipped_count += 1
                continue

            logger.info("Applying migration: %s", version)
            sql = filepath.read_text(encoding="utf-8")

            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                    cur.execute(INSERT_APPLIED, (version,))
                conn.commit()
                logger.info("  ✓ %s applied successfully.", version)
                applied_count += 1
            except Exception as exc:
                conn.rollback()
                logger.error("  ✗ Migration %s failed: %s", version, exc)
                logger.error("Rolling back. Fix the migration and re-run.")
                sys.exit(1)

        logger.info(
            "Migrations complete: %d applied, %d skipped.",
            applied_count,
            skipped_count,
        )
        bootstrap_superadmin(conn)
        logger.info("Bootstrap superadmin is configured from environment variables.")

    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
