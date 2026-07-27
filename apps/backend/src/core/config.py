from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "TerraMind AI"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = ""

    # Geospatial providers
    EARTH_SEARCH_URL: str = "https://earth-search.aws.element84.com/v1"
    TITILER_URL: str = "https://titiler.xyz"
    PROVIDER_TIMEOUT_SECONDS: float = 15.0

    # Redis
    REDIS_URL: str = ""

    # Security
    SECRET_KEY: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

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
