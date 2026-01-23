"""SQLAlchemy engine and session management.

This module exposes:

- `init_engine()`: initializes a global SQLAlchemy engine + session factory.
- `get_db()`: FastAPI dependency that yields a per-request `Session`.

The configuration is driven by Settings (`EMMO_DATABASE_URL` and pool options).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import get_settings


def _make_engine(
    database_url: str,
    *,
    echo: bool,
    pool_pre_ping: bool,
    pool_size: int,
    max_overflow: int,
):
    """Create an engine with reasonable defaults for SQLite and Postgres."""
    connect_args: dict = {}
    engine_kwargs: dict = {
        "echo": echo,
        "pool_pre_ping": pool_pre_ping,
    }
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    else:
        engine_kwargs["pool_size"] = pool_size
        engine_kwargs["max_overflow"] = max_overflow

    return create_engine(database_url, connect_args=connect_args, **engine_kwargs)


engine = None
SessionLocal = None


def init_engine(database_url: str | None = None):
    """(Re)initialize the global engine/sessionmaker.

    Args:
        database_url: Optional override; otherwise uses `Settings.database_url`.

    Notes:
        - For SQLite, `check_same_thread=False` is required for TestClient usage.
        - For remote DBs, pooling parameters are applied.
    """
    global engine, SessionLocal
    settings = get_settings()
    url = database_url or settings.database_url
    engine = _make_engine(
        url,
        echo=settings.db_echo,
        pool_pre_ping=settings.db_pool_pre_ping,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


init_engine()


def get_db():
    """Yield a SQLAlchemy session for a single request and always close it."""
    if SessionLocal is None:
        init_engine()
    db = SessionLocal()  # type: ignore[operator]
    try:
        yield db
    finally:
        db.close()
