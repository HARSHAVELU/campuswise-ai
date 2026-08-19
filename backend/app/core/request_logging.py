"""Per-request logging middleware.

Assigns a short request id, logs method/path/status/duration on every
request, and returns the id in an `X-Request-ID` response header so a
client-reported error can be correlated back to a specific server-side log
line (see docs/architecture-proposal.md, "Observability"). Never logs
request/response bodies -- those can carry credentials or personal data.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        start = time.perf_counter()

        response = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 1)
            status_code = response.status_code if response is not None else 500
            logger.info(
                "request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
