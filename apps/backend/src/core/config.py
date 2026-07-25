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

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
