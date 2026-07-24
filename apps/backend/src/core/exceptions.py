import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.schemas.responses import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """Base application exception."""

    def __init__(self, status_code: int = 400, detail: str = "An error occurred"):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _get_trace_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    trace_id = _get_trace_id(request)
    code = f"APP_{exc.status_code}"
    logger.warning(
        f"AppException: {code} - {exc.detail}",
        extra={
            "request_id": trace_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=exc.detail, trace_id=trace_id)
        ).model_dump(),
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    trace_id = _get_trace_id(request)
    code = f"HTTP_{exc.status_code}"
    message = str(exc.detail)
    logger.warning(
        f"HTTPException: {code} - {message}",
        extra={
            "request_id": trace_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message, trace_id=trace_id)
        ).model_dump(),
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    trace_id = _get_trace_id(request)
    code = "VALIDATION_ERROR"
    message = "Request validation failed"
    logger.warning(
        f"Validation error: {exc.errors()}",
        extra={
            "request_id": trace_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": 422,
        },
    )
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message, trace_id=trace_id)
        ).model_dump(),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    trace_id = _get_trace_id(request)
    code = "INTERNAL_SERVER_ERROR"
    message = "An unexpected error occurred."
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=exc,
        extra={
            "request_id": trace_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": 500,
        },
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=ErrorDetail(code=code, message=message, trace_id=trace_id)
        ).model_dump(),
    )
