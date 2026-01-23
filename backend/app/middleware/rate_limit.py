from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.settings import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Very small in-memory rate limiter.

    Not suitable for multi-worker/multi-instance deployments.
    For production, replace with a shared limiter (Redis) or an API gateway.
    """

    def __init__(self, app):
        super().__init__(app)
        self._bucket: dict[str, tuple[float, int]] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        settings = get_settings()
        limit = int(settings.rate_limit_per_minute or 0)
        if limit <= 0:
            return await call_next(request)

        now = time.monotonic()
        key = request.client.host if request.client else "unknown"
        window_start, count = self._bucket.get(key, (now, 0))
        if now - window_start >= 60.0:
            window_start, count = now, 0

        count += 1
        self._bucket[key] = (window_start, count)

        if count > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )

        return await call_next(request)


__all__ = ["RateLimitMiddleware"]
