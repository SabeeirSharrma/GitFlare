"""Structured logging for GitFlare."""

import logging
import sys
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request with timing."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.monotonic()
        response = await call_next(request)
        elapsed_ms = (time.monotonic() - start) * 1000

        logger = logging.getLogger("gitflare.access")
        logger.info(
            "%s %s -> %d (%.1fms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for GitFlare.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=fmt,
        datefmt=datefmt,
        stream=sys.stderr,
        force=True,
    )

    # Quiet noisy libraries
    for name in ("uvicorn", "uvicorn.access", "uvicorn.error", "httpx"):
        logging.getLogger(name).setLevel(logging.WARNING)

    logger = logging.getLogger("gitflare")
    logger.info("Logging initialized at %s level", level.upper())
