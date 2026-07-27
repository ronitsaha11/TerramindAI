import uuid
from typing import Any, cast

from celery import Celery, Task

from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import (
    InvalidJobOperationError,
    JobCancellationError,
    JobRetryError,
)
from src.async_processing.manager import TaskManager
from src.async_processing.models import JobProgress, JobRecord
from src.async_processing.registry import TaskRegistry


class JobService:
    """
    Application-layer interface for asynchronous execution orchestration.
    Bridges the REST API with the async processing infrastructure.
    """

    def __init__(
        self,
        task_manager: TaskManager,
        task_registry: TaskRegistry,
        celery_app: Celery,
    ) -> None:
        """
        Initialize the JobService.

        Args:
            task_manager: Manager orchestrating job lifecycles.
            task_registry: Registry containing decoupled task definitions.
            celery_app: The Celery application instance acting as the dispatcher.
        """
        self._task_manager = task_manager
        self._task_registry = task_registry
        self._celery_app = celery_app

    def submit_ai_inference(self, payload: dict[str, Any]) -> uuid.UUID:
        """Submit an AI inference background job."""
        task_name = "run_ai_inference_task"
        return self._submit_job(task_name, payload)

    def submit_geospatial_vectorization(self, payload: dict[str, Any]) -> uuid.UUID:
        """Submit a Geospatial vectorization background job."""
        task_name = "run_geospatial_vectorization_task"
        return self._submit_job(task_name, payload)

    def _submit_job(self, task_name: str, payload: dict[str, Any]) -> uuid.UUID:
        """Internal helper to dispatch jobs."""
        # 1. Resolve registered task to verify it exists
        task_func = cast(Task, self._task_registry.lookup(task_name))

        # 2. Create initial job record in PENDING state
        job = self._task_manager.create_job(
            task_name=task_name, metadata={"request_data": payload}
        )

        # 3. Dispatch to Celery using apply_async
        # We pass task_func directly or we can use the signature.
        # But wait, self._task_registry stores the actual Celery `@app.task` object!
        task_func.apply_async(
            kwargs={"job_id_str": str(job.job_id), "request_data": payload},
            task_id=str(job.job_id),
        )

        return job.job_id

    def get_job(self, job_id: uuid.UUID) -> JobRecord:
        """Retrieve a job record."""
        return self._task_manager.get_job(job_id)

    def get_job_status(self, job_id: uuid.UUID) -> JobStatus:
        """Retrieve just the job status."""
        job = self.get_job(job_id)
        return job.status

    def get_job_progress(self, job_id: uuid.UUID) -> JobProgress | None:
        """Retrieve just the job progress."""
        job = self.get_job(job_id)
        return job.progress

    def get_job_result(self, job_id: uuid.UUID) -> str:
        """Retrieve the job result reference. Raises error if incomplete."""
        job = self.get_job(job_id)
        if job.status != JobStatus.SUCCESS or not job.result_reference:
            raise InvalidJobOperationError(
                f"Job {job_id} is not in SUCCESS state or has no result."
            )
        return job.result_reference

    def list_jobs(self) -> list[JobRecord]:
        """List all jobs."""
        return self._task_manager.list_jobs()

    def cancel_job(self, job_id: uuid.UUID) -> JobRecord:
        """Cancel a running or pending job."""
        job = self.get_job(job_id)

        if job.status in (JobStatus.SUCCESS, JobStatus.FAILURE, JobStatus.CANCELLED):
            raise JobCancellationError(
                f"Cannot cancel job in terminal state {job.status.value}"
            )

        # Revoke task in Celery
        self._celery_app.control.revoke(str(job_id), terminate=True)

        # Update lifecycle
        return self._task_manager.cancel_job(job_id)

    def retry_job(self, job_id: uuid.UUID) -> JobRecord:
        """Manually retry a failed or cancelled job."""
        job = self.get_job(job_id)

        if job.status == JobStatus.SUCCESS:
            raise JobRetryError("Cannot retry a successfully completed job.")

        if "request_data" not in job.metadata:
            raise JobRetryError(
                "Cannot retry job: missing original request data in metadata."
            )

        # Re-dispatch Celery task
        task_func = cast(Task, self._task_registry.lookup(job.task_name))

        task_func.apply_async(
            kwargs={
                "job_id_str": str(job.job_id),
                "request_data": job.metadata["request_data"],
            },
            task_id=str(job.job_id),
        )

        # Move back to RETRY state so the worker will transition it to STARTED
        return self._task_manager.mark_retry(job_id)
