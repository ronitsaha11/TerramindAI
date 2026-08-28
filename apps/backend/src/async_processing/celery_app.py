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

# These task modules are imported purely for their side effect: importing them
# registers their tasks on the `app` above. They must come after `app` exists
# (the task modules import it), and nothing references them by name - so E402
# and F401 are both expected. Do NOT let `ruff --fix` remove these; dropping
# them makes FastAPI's enqueue fail with "task not registered" even though the
# worker itself starts fine.
import src.async_processing.tasks.ai_tasks  # noqa: E402, F401
import src.async_processing.tasks.geospatial_tasks  # noqa: E402, F401
