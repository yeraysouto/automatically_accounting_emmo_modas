from app.db.base import Base
from app.db import session

# Ensure models are imported so metadata is populated
from app.db import models  # noqa: F401


def init_db():
    if session.engine is None:
        session.init_engine()
    Base.metadata.create_all(bind=session.engine)
