import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from affine import Affine
from celery.exceptions import Retry

from src.async_processing.exceptions import TaskExecutionError
from src.async_processing.tasks.geospatial_tasks import (
    run_geospatial_vectorization_task,
)
from src.geospatial.exceptions import (
    GeospatialExecutionError,
    GeospatialProcessingError,
)
from src.geospatial.models import GeoJSONExportResult


@pytest.fixture
def mock_geospatial_service() -> MagicMock:
    service = MagicMock()
    # process_mask is a synchronous call
    mock_result = GeoJSONExportResult(
        feature_collection={"type": "FeatureCollection", "features": []},
        export_metadata={"source": "test"},
        export_duration_ms=10.0,
    )
    service.process_mask = MagicMock(return_value=mock_result)
    return service


@pytest.fixture
def mock_task_manager() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_request_data() -> dict[str, Any]:
    return {
        "mask": np.array([[0, 255]]),
        "transform": Affine(1.0, 0.0, 0.0, 0.0, -1.0, 0.0),
        "crs": "EPSG:4326",
    }


@patch("src.async_processing.tasks.geospatial_tasks.get_task_manager")
@patch("src.async_processing.tasks.geospatial_tasks._build_geospatial_service")
def test_run_geospatial_task_success(
    mock_build_service: MagicMock,
    mock_get_manager: MagicMock,
    mock_geospatial_service: MagicMock,
    mock_task_manager: MagicMock,
    dummy_request_data: dict[str, Any],
) -> None:
    mock_build_service.return_value = mock_geospatial_service
    mock_get_manager.return_value = mock_task_manager
    job_id_str = str(uuid.uuid4())

    run_geospatial_vectorization_task(job_id_str, dummy_request_data)

    job_id = uuid.UUID(job_id_str)
    mock_task_manager.acknowledge_receipt.assert_called_once_with(job_id)
    mock_task_manager.start_job.assert_called_once_with(job_id)

    assert mock_task_manager.update_progress.call_count == 2

    mock_geospatial_service.process_mask.assert_called_once()
    mock_task_manager.mark_success.assert_called_once()


@patch("src.async_processing.tasks.geospatial_tasks.get_task_manager")
@patch("src.async_processing.tasks.geospatial_tasks._build_geospatial_service")
def test_run_geospatial_task_transient_retry(
    mock_build_service: MagicMock,
    mock_get_manager: MagicMock,
    mock_geospatial_service: MagicMock,
    mock_task_manager: MagicMock,
    dummy_request_data: dict[str, Any],
) -> None:
    # Simulate a transient connection error wrapped in GeospatialExecutionError
    cause = ConnectionError("Connection dropped")
    exception = GeospatialExecutionError("Pipeline failed")
    exception.__cause__ = cause

    mock_geospatial_service.process_mask.side_effect = exception
    mock_build_service.return_value = mock_geospatial_service
    mock_get_manager.return_value = mock_task_manager
    job_id_str = str(uuid.uuid4())

    with patch.object(
        run_geospatial_vectorization_task, "retry", side_effect=Retry("Retrying task")
    ) as mock_retry:
        with pytest.raises(Retry):
            run_geospatial_vectorization_task(job_id_str, dummy_request_data)

    job_id = uuid.UUID(job_id_str)
    mock_task_manager.mark_retry.assert_called_once_with(job_id)
    mock_retry.assert_called_once()


@patch("src.async_processing.tasks.geospatial_tasks.get_task_manager")
@patch("src.async_processing.tasks.geospatial_tasks._build_geospatial_service")
def test_run_geospatial_task_domain_failure(
    mock_build_service: MagicMock,
    mock_get_manager: MagicMock,
    mock_geospatial_service: MagicMock,
    mock_task_manager: MagicMock,
    dummy_request_data: dict[str, Any],
) -> None:
    # Simulate a non-transient domain error wrapped in GeospatialExecutionError
    cause = GeospatialProcessingError("Invalid geometry")
    exception = GeospatialExecutionError("Pipeline failed")
    exception.__cause__ = cause

    mock_geospatial_service.process_mask.side_effect = exception
    mock_build_service.return_value = mock_geospatial_service
    mock_get_manager.return_value = mock_task_manager
    job_id_str = str(uuid.uuid4())

    with patch.object(run_geospatial_vectorization_task, "retry") as mock_retry:
        with pytest.raises(TaskExecutionError, match="Pipeline failed"):
            run_geospatial_vectorization_task(job_id_str, dummy_request_data)

    job_id = uuid.UUID(job_id_str)
    mock_task_manager.mark_failure.assert_called_once_with(
        job_id, error_message="Pipeline failed"
    )
    mock_retry.assert_not_called()
