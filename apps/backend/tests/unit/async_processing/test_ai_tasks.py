import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from celery.exceptions import Retry

from src.ai.exceptions import InferenceValidationError, ModelLoadError
from src.ai.models import InferenceResult, PredictionMetadata
from src.async_processing.exceptions import TaskExecutionError
from src.async_processing.tasks.ai_tasks import run_ai_inference_task


@pytest.fixture
def mock_ai_service() -> MagicMock:
    service = MagicMock()
    # execute_inference is async, so we need an AsyncMock
    mock_result = InferenceResult(
        request_id=uuid.uuid4(),
        prediction_metadata=PredictionMetadata(
            execution_time_ms=10.0, model_version="1.0"
        ),
        result_data={},
    )
    service.execute_inference = AsyncMock(return_value=mock_result)
    return service


@pytest.fixture
def mock_task_manager() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_request_data() -> dict[str, Any]:
    return {
        "project_id": str(uuid.uuid4()),
        "scene_id": "scene-123",
        "model_id": "segformer-b0",
        "parameters": {"raw_data": [[0, 255]]},
    }


@patch("src.async_processing.tasks.ai_tasks.get_task_manager")
@patch("src.async_processing.tasks.ai_tasks._build_ai_service")
def test_run_ai_inference_task_success(
    mock_build_service: MagicMock,
    mock_get_manager: MagicMock,
    mock_ai_service: MagicMock,
    mock_task_manager: MagicMock,
    dummy_request_data: dict[str, Any],
) -> None:
    mock_build_service.return_value = mock_ai_service
    mock_get_manager.return_value = mock_task_manager
    job_id_str = str(uuid.uuid4())

    # We do not pass `mock_task` because Celery injects `self` automatically
    run_ai_inference_task(job_id_str, dummy_request_data)

    # Verify lifecycle updates
    job_id = uuid.UUID(job_id_str)
    mock_task_manager.acknowledge_receipt.assert_called_once_with(job_id)
    mock_task_manager.start_job.assert_called_once_with(job_id)

    # Verify progress was emitted
    assert mock_task_manager.update_progress.call_count == 2

    # Verify the service was called
    mock_ai_service.execute_inference.assert_called_once()

    # Verify success was marked
    mock_task_manager.mark_success.assert_called_once()


@patch("src.async_processing.tasks.ai_tasks.get_task_manager")
@patch("src.async_processing.tasks.ai_tasks._build_ai_service")
def test_run_ai_inference_task_transient_retry(
    mock_build_service: MagicMock,
    mock_get_manager: MagicMock,
    mock_ai_service: MagicMock,
    mock_task_manager: MagicMock,
    dummy_request_data: dict[str, Any],
) -> None:
    mock_ai_service.execute_inference.side_effect = ModelLoadError("Temporary failure")
    mock_build_service.return_value = mock_ai_service
    mock_get_manager.return_value = mock_task_manager
    job_id_str = str(uuid.uuid4())

    # Mock retry on the task object itself
    with patch.object(
        run_ai_inference_task, "retry", side_effect=Retry("Retrying task")
    ) as mock_retry:
        with pytest.raises(Retry):
            run_ai_inference_task(job_id_str, dummy_request_data)

    job_id = uuid.UUID(job_id_str)
    mock_task_manager.mark_retry.assert_called_once_with(job_id)
    mock_retry.assert_called_once()


@patch("src.async_processing.tasks.ai_tasks.get_task_manager")
@patch("src.async_processing.tasks.ai_tasks._build_ai_service")
def test_run_ai_inference_task_domain_failure(
    mock_build_service: MagicMock,
    mock_get_manager: MagicMock,
    mock_ai_service: MagicMock,
    mock_task_manager: MagicMock,
    dummy_request_data: dict[str, Any],
) -> None:
    mock_ai_service.execute_inference.side_effect = InferenceValidationError(
        "Bad request"
    )
    mock_build_service.return_value = mock_ai_service
    mock_get_manager.return_value = mock_task_manager
    job_id_str = str(uuid.uuid4())

    with patch.object(run_ai_inference_task, "retry") as mock_retry:
        with pytest.raises(TaskExecutionError, match="Bad request"):
            run_ai_inference_task(job_id_str, dummy_request_data)

    job_id = uuid.UUID(job_id_str)
    mock_task_manager.mark_failure.assert_called_once_with(
        job_id, error_message="Bad request"
    )
    mock_retry.assert_not_called()
