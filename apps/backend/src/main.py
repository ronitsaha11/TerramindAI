import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.v1.router import api_router
from src.core.config import settings
from src.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from src.core.logging import setup_logging
from src.core.redis import redis_client
from src.db.session import engine
from src.middleware.logging import RequestLoggingMiddleware
from src.middleware.security import SecurityHeadersMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Lifecycle events for the FastAPI application.
    """
    # Startup
    setup_logging(log_level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode.")

    app.state.earth_search_client = httpx.AsyncClient(
        base_url=settings.EARTH_SEARCH_URL,
        timeout=settings.PROVIDER_TIMEOUT_SECONDS,
    )
    app.state.titiler_client = httpx.AsyncClient(
        base_url=settings.TITILER_URL,
        timeout=settings.PROVIDER_TIMEOUT_SECONDS,
    )

    try:
        # Verify configurations and initialize connections
        await redis_client.connect()
        logger.info("Redis client connected.")
        yield
    except Exception as e:
        logger.error(f"Application lifecycle error: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application...")
        await app.state.earth_search_client.aclose()
        await app.state.titiler_client.aclose()

        try:
            await redis_client.disconnect()
            logger.info("Redis client disconnected.")
        except Exception as e:
            logger.error(f"Error during Redis disconnect: {e}")

        try:
            await engine.dispose()
            logger.info("Database engine disposed.")
        except Exception as e:
            logger.error(f"Error during Database dispose: {e}")


def create_app() -> FastAPI:
    """
    Application factory for the FastAPI application.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        description="Earth Intelligence Platform for Satellite Image Analysis",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Register Exception Handlers
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Register Middlewares (Order matters: outermost first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Register API Routers
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
