from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.init_db import init_db
from app.settings import get_settings


def create_app() -> FastAPI:
    app = FastAPI(title="EMMA Accounting OCR API")

    @app.on_event("startup")
    def _startup():
        init_db()

    settings = get_settings()
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(router)
    return app


app = create_app()
