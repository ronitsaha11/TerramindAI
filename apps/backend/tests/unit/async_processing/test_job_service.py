import datetime
import uuid
from unittest.mock import MagicMock

import pytest

from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import (
    InvalidJobOperationError,
    JobCancellationError,
    JobNotFoundError,
    JobRetryError,
)
from src.async_processing.models import JobProgress, JobRecord
from src.async_processing.service import JobService


@pytest.fixture
def mock_task_manager() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_task_registry() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_celery_app() -> MagicMock:
    app = MagicMock()
    app.control = MagicMock()
    return app


@pytest.fixture
def job_service(
    mock_task_manager: MagicMock,
    mock_task_registry: MagicMock,
    mock_celery_app: MagicMock,
) -> JobService:
    return JobService(
        task_manager=mock_task_manager,
        task_registry=mock_task_registry,
        celery_app=mock_celery_app,
    )


def test_submit_ai_inference(
    job_service: JobService,
    mock_task_manager: MagicMock,
    mock_task_registry: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="run_ai_inference_task",
        status=JobStatus.PENDING,
        created_at=now,
        updated_at=now,
        metadata={"request_data": {"data": 123}},
    )
    mock_task_manager.create_job.return_value = mock_job
    mock_task = MagicMock()
    mock_task_registry.lookup.return_value = mock_task

    returned_id = job_service.submit_ai_inference({"data": 123})

    assert returned_id == job_id
    mock_task_registry.lookup.assert_called_once_with("run_ai_inference_task")
    mock_task_manager.create_job.assert_called_once()
    mock_task.apply_async.assert_called_once_with(
        kwargs={"job_id_str": str(job_id), "request_data": {"data": 123}},
        task_id=str(job_id),
    )


def test_submit_geospatial_vectorization(
    job_service: JobService,
    mock_task_manager: MagicMock,
    mock_task_registry: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="run_geospatial_vectorization_task",
        status=JobStatus.PENDING,
        created_at=now,
        updated_at=now,
        metadata={"request_data": {"geo": "spatial"}},
    )
    mock_task_manager.create_job.return_value = mock_job
    mock_task = MagicMock()
    mock_task_registry.lookup.return_value = mock_task

    returned_id = job_service.submit_geospatial_vectorization({"geo": "spatial"})

    assert returned_id == job_id
    mock_task_registry.lookup.assert_called_once_with(
        "run_geospatial_vectorization_task"
    )
    mock_task.apply_async.assert_called_once()


def test_get_job_queries(
    job_service: JobService,
    mock_task_manager: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    progress = JobProgress(percentage=50.0, current_step=1, total_steps=2)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test_task",
        status=JobStatus.SUCCESS,
        created_at=now,
        updated_at=now,
        progress=progress,
        result_reference="s3://results/1.json",
    )
    mock_task_manager.get_job.return_value = mock_job

    assert job_service.get_job(job_id) == mock_job
    assert job_service.get_job_status(job_id) == JobStatus.SUCCESS
    assert job_service.get_job_progress(job_id) == progress
    assert job_service.get_job_result(job_id) == "s3://results/1.json"


def test_get_job_result_incomplete(
    job_service: JobService,
    mock_task_manager: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test_task",
        status=JobStatus.PROCESSING,
        created_at=now,
        updated_at=now,
    )
    mock_task_manager.get_job.return_value = mock_job

    with pytest.raises(InvalidJobOperationError, match="not in SUCCESS state"):
        job_service.get_job_result(job_id)


def test_cancel_job_success(
    job_service: JobService,
    mock_task_manager: MagicMock,
    mock_celery_app: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test",
        status=JobStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    mock_task_manager.get_job.return_value = mock_job

    job_service.cancel_job(job_id)

    mock_celery_app.control.revoke.assert_called_once_with(str(job_id), terminate=True)
    mock_task_manager.cancel_job.assert_called_once_with(job_id)


def test_cancel_job_terminal_rejection(
    job_service: JobService,
    mock_task_manager: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test",
        status=JobStatus.SUCCESS,
        created_at=now,
        updated_at=now,
    )
    mock_task_manager.get_job.return_value = mock_job

    with pytest.raises(JobCancellationError, match="terminal state"):
        job_service.cancel_job(job_id)


def test_retry_job_success(
    job_service: JobService,
    mock_task_manager: MagicMock,
    mock_task_registry: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test_task",
        status=JobStatus.FAILURE,
        created_at=now,
        updated_at=now,
        metadata={"request_data": {"param": 1}},
    )
    mock_task_manager.get_job.return_value = mock_job
    mock_task = MagicMock()
    mock_task_registry.lookup.return_value = mock_task

    job_service.retry_job(job_id)

    mock_task_registry.lookup.assert_called_once_with("test_task")
    mock_task.apply_async.assert_called_once_with(
        kwargs={"job_id_str": str(job_id), "request_data": {"param": 1}},
        task_id=str(job_id),
    )
    mock_task_manager.mark_retry.assert_called_once_with(job_id)


def test_retry_job_success_rejection(
    job_service: JobService,
    mock_task_manager: MagicMock,
) -> None:
    job_id = uuid.uuid4()
    now = datetime.datetime.now(datetime.UTC)
    mock_job = JobRecord(
        job_id=job_id,
        task_name="test",
        status=JobStatus.SUCCESS,
        created_at=now,
        updated_at=now,
    )
    mock_task_manager.get_job.return_value = mock_job

    with pytest.raises(JobRetryError, match="successfully completed"):
        job_service.retry_job(job_id)


def test_unknown_job_error(
    job_service: JobService,
    mock_task_manager: MagicMock,
) -> None:
    mock_task_manager.get_job.side_effect = JobNotFoundError("Not found")
    job_id = uuid.uuid4()

    with pytest.raises(JobNotFoundError):
        job_service.get_job(job_id)
