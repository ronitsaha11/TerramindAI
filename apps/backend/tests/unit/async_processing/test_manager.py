import pytest

from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import JobStateError
from src.async_processing.interfaces import InMemoryJobStore
from src.async_processing.manager import TaskManager
from src.async_processing.models import JobProgress


@pytest.fixture
def manager() -> TaskManager:
    store = InMemoryJobStore()
    return TaskManager(store=store)


def test_manager_job_creation(manager: TaskManager) -> None:
    job = manager.create_job(task_name="test_task", metadata={"key": "value"})
    assert job.task_name == "test_task"
    assert job.status == JobStatus.PENDING
    assert job.metadata == {"key": "value"}


def test_manager_valid_lifecycle(manager: TaskManager) -> None:
    job = manager.create_job("test_task")

    job = manager.acknowledge_receipt(job.job_id)
    assert job.status == JobStatus.RECEIVED

    job = manager.start_job(job.job_id)
    assert job.status == JobStatus.STARTED

    progress = JobProgress(percentage=50.0, current_step=1, total_steps=2)
    job = manager.update_progress(job.job_id, progress)
    assert job.status == JobStatus.PROCESSING
    assert job.progress == progress

    job = manager.mark_success(job.job_id, "s3://result")
    assert job.status == JobStatus.SUCCESS
    assert job.result_reference == "s3://result"
    assert job.progress is not None
    assert job.progress.percentage == 100.0


def test_manager_invalid_transition(manager: TaskManager) -> None:
    job = manager.create_job("test_task")

    # Cannot go from PENDING straight to SUCCESS
    with pytest.raises(JobStateError, match="Cannot transition job"):
        manager.mark_success(job.job_id, "s3://result")


def test_manager_failure_recording(manager: TaskManager) -> None:
    job = manager.create_job("test_task")
    job = manager.start_job(job.job_id)
    job = manager.mark_failure(job.job_id, "Division by zero")

    assert job.status == JobStatus.FAILURE
    assert job.error_message == "Division by zero"


def test_manager_retry(manager: TaskManager) -> None:
    job = manager.create_job("test_task")
    job = manager.start_job(job.job_id)
    job = manager.mark_retry(job.job_id)

    assert job.status == JobStatus.RETRY


def test_manager_cancellation(manager: TaskManager) -> None:
    job = manager.create_job("test_task")
    job = manager.start_job(job.job_id)
    job = manager.cancel_job(job.job_id)

    assert job.status == JobStatus.CANCELLED
