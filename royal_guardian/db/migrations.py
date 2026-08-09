from __future__ import annotations
from sqlalchemy import inspect, text
from royal_guardian.db.base import engine

MIGRATIONS=[
    (1, {
        "users": [
            ("email_verified", "BOOLEAN NOT NULL DEFAULT {false}"),
            ("mfa_enabled", "BOOLEAN NOT NULL DEFAULT {false}"),
            ("mfa_secret_encrypted", "TEXT NOT NULL DEFAULT ''"),
        ],
        "workflows": [
            ("schedule_interval_seconds", "INTEGER NOT NULL DEFAULT 0"),
            ("next_run_at", "TIMESTAMP NULL"),
        ],
    }),
]

def apply_migrations() -> None:
    false="FALSE" if engine.dialect.name.startswith("postgres") else "0"
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
        applied={r[0] for r in conn.execute(text("SELECT version FROM schema_migrations"))}
        inspector=inspect(conn)
        for version,tables in MIGRATIONS:
            if version in applied: continue
            for table,columns in tables.items():
                if table not in inspector.get_table_names(): continue
                existing={c["name"] for c in inspector.get_columns(table)}
                for name,ddl in columns:
                    if name not in existing:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl.format(false=false)}"))
            conn.execute(text("INSERT INTO schema_migrations(version) VALUES (:v)"),{"v":version})
