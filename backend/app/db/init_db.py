from app.db.base import Base
from app.db.session import engine

# Ensure models are imported so metadata is populated
from app.db import models  # noqa: F401


def init_db():
    Base.metadata.create_all(bind=engine)
