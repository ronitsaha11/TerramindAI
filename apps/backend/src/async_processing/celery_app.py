from celery import Celery

from src.async_processing.config import get_celery_config
from src.core.config import settings

# Initialize the Celery application singleton
app = Celery(settings.APP_NAME)

# Apply settings from the config mapper
app.conf.update(**get_celery_config())

# Strict configuration overrides for deterministic reliability
app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    task_ignore_result=False,
)

# Autodiscover tasks from registered apps/packages
app.autodiscover_tasks(["src.async_processing"])

# Explicitly import task modules to ensure they are registered with Celery and TaskRegistry
import src.async_processing.tasks.ai_tasks  # noqa: F401
import src.async_processing.tasks.geospatial_tasks  # noqa: F401
