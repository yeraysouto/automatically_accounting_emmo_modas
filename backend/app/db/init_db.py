"""Database bootstrap helpers.

This module exists to support development and tests.

- In dev/test, we can create tables automatically via `Base.metadata.create_all`.
- In production (Postgres + scaling), prefer Alembic migrations and set
    `EMMO_DB_AUTO_CREATE=false`.
"""

from app.db.base import Base
from app.db import session
from app.settings import get_settings

# Ensure models are imported so metadata is populated
from app.db import models  # noqa: F401


def init_db():
    """Create tables if `db_auto_create` is enabled."""
    if not get_settings().db_auto_create:
        return
    if session.engine is None:
        session.init_engine()
    Base.metadata.create_all(bind=session.engine)
