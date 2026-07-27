from unittest.mock import patch

from celery import Celery

from src.async_processing.celery_app import app
from src.async_processing.config import get_celery_config
from src.core.config import settings


def test_celery_singleton_initialization():
    """Verify the Celery app is instantiated correctly."""
    assert isinstance(app, Celery)
    assert app.main == settings.APP_NAME


def test_celery_config_mapping():
    """Verify that configuration mappings match environment settings."""
    config = get_celery_config()

    assert config["broker_url"] == settings.CELERY_BROKER_URL
    assert config["result_backend"] == settings.CELERY_RESULT_BACKEND
    assert config["task_serializer"] == "json"
    assert config["result_serializer"] == "json"
    assert config["accept_content"] == ["json"]
    assert config["timezone"] == "UTC"
    assert config["enable_utc"] is True
    assert config["result_expires"] == 3600
    assert config["task_default_queue"] == "celery"
    assert config["worker_prefetch_multiplier"] == 1


def test_celery_app_configuration_applied():
    """Verify that strict override settings were applied to the singleton."""
    # Check overrides
    assert app.conf.task_track_started is True
    assert app.conf.task_acks_late is True
    assert app.conf.task_ignore_result is False

    # Check mappings
    assert app.conf.broker_url == settings.CELERY_BROKER_URL
    assert app.conf.result_backend == settings.CELERY_RESULT_BACKEND
    assert app.conf.task_serializer == "json"
    assert app.conf.result_serializer == "json"
    assert app.conf.accept_content == ["json"]
    assert app.conf.timezone == "UTC"
    assert app.conf.enable_utc is True
    assert app.conf.result_expires == 3600
    assert app.conf.task_default_queue == "celery"
    assert app.conf.worker_prefetch_multiplier == 1


@patch("src.async_processing.celery_app.Celery.autodiscover_tasks")
def test_autodiscovery_enabled(mock_autodiscover):
    """Verify that task autodiscovery is triggered during initialization."""
    # Since the module is already loaded, we have to reload it to trigger the mock
    import importlib

    import src.async_processing.celery_app

    importlib.reload(src.async_processing.celery_app)

    mock_autodiscover.assert_called_once_with(["src.async_processing"])
