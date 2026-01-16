from fastapi import FastAPI

from app.api.routes import router
from app.db.init_db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="EMMA Accounting OCR API")

    @app.on_event("startup")
    def _startup():
        init_db()

    app.include_router(router)
    return app


app = create_app()
