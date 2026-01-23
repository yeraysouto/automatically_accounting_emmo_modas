from __future__ import annotations

"""Wait until Postgres is reachable.

Used by `docker compose run --rm migrate` to avoid running Alembic before the DB
accepts connections.

Inputs:
- `EMMO_DATABASE_URL`: SQLAlchemy URL (postgresql+psycopg://... recommended)
- `EMMO_DB_WAIT_TIMEOUT_S`: optional timeout (default 60)
"""

import os
import time

import psycopg


def _psycopg_dsn_from_sqlalchemy_url(sqlalchemy_url: str) -> str:
    # Alembic/SQLAlchemy commonly use: postgresql+psycopg://user:pass@host:5432/db
    if sqlalchemy_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + sqlalchemy_url.removeprefix("postgresql+psycopg://")
    return sqlalchemy_url


def main() -> int:
    sqlalchemy_url = os.environ.get("EMMO_DATABASE_URL")
    if not sqlalchemy_url:
        raise SystemExit("EMMO_DATABASE_URL is required")

    dsn = _psycopg_dsn_from_sqlalchemy_url(sqlalchemy_url)

    timeout_s = int(os.environ.get("EMMO_DB_WAIT_TIMEOUT_S", "60"))
    deadline = time.time() + timeout_s

    last_exc: Exception | None = None
    while time.time() < deadline:
        try:
            with psycopg.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            print("postgres ready")
            return 0
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            time.sleep(1)

    raise SystemExit(f"postgres not ready after {timeout_s}s: {last_exc}")


if __name__ == "__main__":
    raise SystemExit(main())
