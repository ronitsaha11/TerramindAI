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
# (Placeholder for future task modules)
app.autodiscover_tasks(["src.async_processing"])
