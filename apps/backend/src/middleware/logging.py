import logging
import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        # Set on request state for error handlers
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time

            # Append headers to the response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(duration)

            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"{response.status_code}",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": response.status_code,
                    "duration": duration,
                },
            )
            return response

        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=e,
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                    "status_code": 500,
                    "duration": duration,
                },
            )
            raise e
