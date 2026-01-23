from __future__ import annotations

"""FastAPI application factory.

`create_app()` wires together:
- logging,
- middleware (request id, security headers, optional trusted hosts / HTTPS redirect / rate limit),
- and API routes.

Database initialization is handled in the app lifespan; in production with Postgres
and Alembic you typically disable `EMMO_DB_AUTO_CREATE` and run migrations instead.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import router
from app.db.init_db import init_db
from app.logging_config import configure_logging
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_context import RequestContextMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.settings import get_settings


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    configure_logging()

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        """App lifespan hook used for DB bootstrap in dev."""
        init_db()
        yield

    app = FastAPI(title="EMMO Accounting OCR API", lifespan=lifespan)

    settings = get_settings()
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    if settings.rate_limit_per_minute and settings.rate_limit_per_minute > 0:
        app.add_middleware(RateLimitMiddleware)

    if settings.enable_trusted_hosts and settings.trusted_hosts:
        allowed = [h.strip() for h in settings.trusted_hosts.split(",") if h.strip()]
        if allowed:
            app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed)

    if settings.https_redirect:
        app.add_middleware(HTTPSRedirectMiddleware)
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
