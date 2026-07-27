from typing import Any

from src.core.config import settings


def get_celery_config() -> dict[str, Any]:
    """
    Extract Celery-specific configuration from the global application settings.

    Returns:
        Dictionary containing kwargs suitable for celery.app.conf.update()
    """
    return {
        "broker_url": settings.CELERY_BROKER_URL,
        "result_backend": settings.CELERY_RESULT_BACKEND,
        "task_serializer": settings.CELERY_TASK_SERIALIZER,
        "result_serializer": settings.CELERY_RESULT_SERIALIZER,
        "accept_content": settings.CELERY_ACCEPT_CONTENT,
        "timezone": settings.CELERY_TIMEZONE,
        "enable_utc": settings.CELERY_ENABLE_UTC,
        "result_expires": settings.CELERY_RESULT_EXPIRES,
        "task_default_queue": settings.CELERY_DEFAULT_QUEUE,
        "worker_prefetch_multiplier": settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    }
