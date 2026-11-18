"""Job submission and manual retry against the real TaskManager.

These use the in-memory job store rather than a mocked TaskManager, because
the defects they guard against lived in the interaction between JobService and
the real state machine: a mocked manager accepts any transition.
"""

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
from kombu.exceptions import OperationalError

from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import (
    JobDispatchError,
    JobRetryError,
    JobStateError,
)
from src.async_processing.interfaces import InMemoryJobStore
from src.async_processing.manager import TaskManager
from src.async_processing.service import JobService

BROKER_ERROR = "Error 111 connecting to redis://:hunter2@broker:6379/0"


class FakeTask:
    """Stands in for a Celery task; records dispatches or fails like a broker."""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict[str, Any]] = []

    def apply_async(self, kwargs: dict[str, Any], task_id: str) -> None:
        if self.fail:
            raise OperationalError(BROKER_ERROR)
        self.calls.append({"kwargs": kwargs, "task_id": task_id})


@pytest.fixture
def manager() -> TaskManager:
    return TaskManager(InMemoryJobStore())


def make_service(manager: TaskManager, task: FakeTask) -> JobService:
    registry = MagicMock()
    registry.lookup.return_value = task
    return JobService(
        task_manager=manager, task_registry=registry, celery_app=MagicMock()
    )


def job_in_state(manager: TaskManager, *path: JobStatus) -> uuid.UUID:
    """Create a job and walk it through valid worker transitions."""
    job = manager.create_job("run_ai_inference_task", {"request_data": {"x": 1}})
    for status in path:
        if status == JobStatus.STARTED:
            manager.start_job(job.job_id)
        elif status == JobStatus.FAILURE:
            manager.mark_failure(job.job_id, "boom")
        elif status == JobStatus.CANCELLED:
            manager.cancel_job(job.job_id)
        elif status == JobStatus.RETRY:
            manager.mark_retry(job.job_id)
    return job.job_id


# --- submission ------------------------------------------------------------


def test_submit_dispatches_with_job_id_as_task_id(manager: TaskManager) -> None:
    task = FakeTask()
    job_id = make_service(manager, task).submit_ai_inference({"x": 1})

    assert task.calls == [
        {
            "kwargs": {"job_id_str": str(job_id), "request_data": {"x": 1}},
            "task_id": str(job_id),
        }
    ]
    assert manager.get_job(job_id).status == JobStatus.PENDING


def test_submit_with_broker_down_fails_the_job_instead_of_leaving_it_pending(
    manager: TaskManager,
) -> None:
    service = make_service(manager, FakeTask(fail=True))

    with pytest.raises(JobDispatchError) as raised:
        service.submit_ai_inference({"x": 1})

    assert raised.value.status_code == 503
    [job] = manager.list_jobs()
    assert job.status == JobStatus.FAILURE
    # Neither the stored record nor the API error repeats the broker URL.
    assert "hunter2" not in (job.error_message or "")
    assert "hunter2" not in raised.value.detail


# --- manual retry ----------------------------------------------------------


@pytest.mark.parametrize("terminal", [JobStatus.FAILURE, JobStatus.CANCELLED])
def test_retry_requeues_a_failed_or_cancelled_job_and_dispatches_once(
    manager: TaskManager, terminal: JobStatus
) -> None:
    path = (
        (JobStatus.STARTED, terminal) if terminal == JobStatus.FAILURE else (terminal,)
    )
    job_id = job_in_state(manager, *path)
    task = FakeTask()

    updated = make_service(manager, task).retry_job(job_id)

    assert updated.status == JobStatus.RETRY
    assert manager.get_job(job_id).status == JobStatus.RETRY
    assert len(task.calls) == 1
    # The worker can now pick it up: RETRY -> STARTED is a valid transition.
    assert manager.start_job(job_id).status == JobStatus.STARTED


@pytest.mark.parametrize(
    "path",
    [
        (),  # PENDING
        (JobStatus.STARTED,),
        (JobStatus.STARTED, JobStatus.RETRY),
    ],
    ids=["pending", "started", "retrying"],
)
def test_retry_of_an_active_job_is_rejected_without_dispatching(
    manager: TaskManager, path: tuple[JobStatus, ...]
) -> None:
    job_id = job_in_state(manager, *path)
    before = manager.get_job(job_id).status
    task = FakeTask()

    with pytest.raises(JobRetryError, match="Only failed or cancelled"):
        make_service(manager, task).retry_job(job_id)

    assert task.calls == []  # no second execution queued
    assert manager.get_job(job_id).status == before


def test_retry_with_broker_down_marks_the_job_failed(manager: TaskManager) -> None:
    job_id = job_in_state(manager, JobStatus.STARTED, JobStatus.FAILURE)

    with pytest.raises(JobDispatchError):
        make_service(manager, FakeTask(fail=True)).retry_job(job_id)

    assert manager.get_job(job_id).status == JobStatus.FAILURE


# --- the worker state table is unchanged ------------------------------------


def test_worker_still_cannot_revive_a_failed_or_cancelled_job(
    manager: TaskManager,
) -> None:
    failed = job_in_state(manager, JobStatus.STARTED, JobStatus.FAILURE)
    cancelled = job_in_state(manager, JobStatus.CANCELLED)

    for job_id in (failed, cancelled):
        with pytest.raises(JobStateError):
            manager.mark_retry(job_id)


def test_dispatch_failure_cannot_be_recorded_for_a_running_job(
    manager: TaskManager,
) -> None:
    job_id = job_in_state(manager, JobStatus.STARTED)

    with pytest.raises(JobStateError):
        manager.mark_dispatch_failed(job_id, "x")

    assert manager.get_job(job_id).status == JobStatus.STARTED
