from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.settings import get_settings


def _make_engine(database_url: str):
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    return create_engine(database_url, connect_args=connect_args)


engine = None
SessionLocal = None


def init_engine(database_url: str | None = None):
    global engine, SessionLocal
    url = database_url or get_settings().database_url
    engine = _make_engine(url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


init_engine()


def get_db():
    if SessionLocal is None:
        init_engine()
    db = SessionLocal()  # type: ignore[operator]
    try:
        yield db
    finally:
        db.close()
