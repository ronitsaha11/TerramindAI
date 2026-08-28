from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TerraMind AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    # Points at the local docker-compose Postgres (see .env.example and
    # docker-compose.yml). Like REDIS_URL this must stay parseable: the async
    # engine is created at module scope in src/db/session.py, so an empty value
    # breaks importing the API rather than failing on first query.
    DATABASE_URL: str = (
        "postgresql+asyncpg://terramind:terramind_local@localhost:5432/terramind_db"
    )

    # Geospatial providers
    EARTH_SEARCH_URL: str = "https://earth-search.aws.element84.com/v1"
    TITILER_URL: str = "https://titiler.xyz"
    PROVIDER_TIMEOUT_SECONDS: float = 15.0

    # Redis
    # Defaults to the same local Redis the CELERY_* URLs below point at. It must
    # stay a parseable redis:// URL: RedisJobStore is constructed at module scope
    # (src/async_processing/manager.py), so an empty value makes importing
    # src.api.dependencies fail outright rather than at connect time.
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    SECRET_KEY: str = ""

    # Claude API - natural-language spatial queries
    # Server-side only. This key is never sent to the frontend, and the model is
    # only ever asked to interpret intent: it receives no feature data, no
    # identifiers, and issues no queries of its own. Left unset, /query/natural
    # returns 503 and every other endpoint keeps working.
    ANTHROPIC_API_KEY: str = ""
    NLQ_MODEL: str = "claude-opus-5"

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    # ALLOWED_ORIGINS is the canonical variable controlling CORS; it is applied
    # by CORSMiddleware in src/main.py. Being list[str], pydantic-settings parses
    # it as JSON, so .env must supply a JSON array - a comma-separated string is
    # rejected. See apps/backend/.env.example.
    # The default targets the Vite dev server (see scripts/start_stack.ps1);
    # localhost and 127.0.0.1 are distinct origins to the browser.
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5273",
        "http://127.0.0.1:5273",
    ]

    # Celery & Async Processing
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_RESULT_EXPIRES: int = 3600
    CELERY_DEFAULT_QUEUE: str = "celery"
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
