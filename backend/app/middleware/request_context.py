from __future__ import annotations

"""Request-scoped context (request id).

This middleware:
- Accepts an incoming `X-Request-ID` if provided (e.g. from a gateway), otherwise generates one.
- Stores it in a contextvar (`request_id_ctx`) so logging can include it.
- Echoes it back on the response header.
"""

import contextvars
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a stable request id to the request and response."""
    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get("X-Request-ID")
        request_id = incoming.strip() if incoming and incoming.strip() else uuid4().hex
        token = request_id_ctx.set(request_id)
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)

        response.headers.setdefault("X-Request-ID", request_id)
        return response


__all__ = ["RequestContextMiddleware", "request_id_ctx"]
