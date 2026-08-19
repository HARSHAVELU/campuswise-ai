"""Global fallback for unhandled exceptions.

Every specific, expected failure (not found, validation, auth) already gets
a clean response from FastAPI/route code. This is the last-resort net: it
guarantees a client never sees a raw Python traceback or internal error
detail, while the real exception is still fully logged server-side for
debugging (see docs/architecture-proposal.md, "Error Handling").
"""

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception processing %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "internal_error",
            "message": "Something went wrong on our end. Please try again in a moment.",
        },
    )
