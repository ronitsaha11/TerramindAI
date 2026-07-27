import logging

from src.async_processing.celery_app import app

logger = logging.getLogger(__name__)

# This file acts as the entry point for the Celery worker.
# It can be started using the CLI:
# `celery -A src.async_processing.worker worker -l info`

if __name__ == "__main__":
    logger.info("Starting TerraMind AI Celery worker...")
    app.start()
