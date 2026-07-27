import datetime
import uuid
from typing import Any

from src.async_processing.enums import JobStatus
from src.async_processing.exceptions import JobStateError
from src.async_processing.interfaces import InMemoryJobStore, JobStoreProtocol
from src.async_processing.models import JobProgress, JobRecord

# Valid transitions from a specific JobStatus to a list of allowed next states.
# Any transition not explicitly defined here raises a JobStateError.
_VALID_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.PENDING: {JobStatus.RECEIVED, JobStatus.STARTED, JobStatus.CANCELLED},
    JobStatus.RECEIVED: {JobStatus.STARTED, JobStatus.CANCELLED},
    JobStatus.STARTED: {
        JobStatus.PROCESSING,
        JobStatus.SUCCESS,
        JobStatus.FAILURE,
        JobStatus.RETRY,
        JobStatus.CANCELLED,
    },
    JobStatus.PROCESSING: {
        JobStatus.SUCCESS,
        JobStatus.FAILURE,
        JobStatus.RETRY,
        JobStatus.CANCELLED,
    },
    JobStatus.RETRY: {JobStatus.STARTED, JobStatus.CANCELLED},
    # SUCCESS, FAILURE, CANCELLED are terminal states and have no outgoing transitions.
    JobStatus.SUCCESS: set(),
    JobStatus.FAILURE: set(),
    JobStatus.CANCELLED: set(),
}


class TaskManager:
    """
    Application-layer orchestrator for the job lifecycle.
    Maintains backend-agnostic boundaries.
    """

    def __init__(self, store: JobStoreProtocol) -> None:
        self._store = store

    def _transition(self, current_status: JobStatus, next_status: JobStatus) -> None:
        """Validate if transitioning to next_status is allowed."""
        if next_status not in _VALID_TRANSITIONS[current_status]:
            raise JobStateError(
                f"Cannot transition job from {current_status.value} "
                f"to {next_status.value}"
            )

    def create_job(
        self, task_name: str, metadata: dict[str, Any] | None = None
    ) -> JobRecord:
        """Initialize a new job in the PENDING state."""
        now = datetime.datetime.now(datetime.UTC)
        job = JobRecord(
            job_id=uuid.uuid4(),
            task_name=task_name,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._store.create_job(job)
        return job

    def acknowledge_receipt(self, job_id: uuid.UUID) -> JobRecord:
        """Mark that the job was received by the broker/worker."""
        job = self._store.get_job(job_id)
        self._transition(job.status, JobStatus.RECEIVED)

        updated_job = job.model_copy(
            update={
                "status": JobStatus.RECEIVED,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job

    def start_job(self, job_id: uuid.UUID) -> JobRecord:
        """Mark the job as STARTED."""
        job = self._store.get_job(job_id)
        self._transition(job.status, JobStatus.STARTED)

        updated_job = job.model_copy(
            update={
                "status": JobStatus.STARTED,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job

    def update_progress(self, job_id: uuid.UUID, progress: JobProgress) -> JobRecord:
        """Update job progress and mark it as PROCESSING if not already."""
        job = self._store.get_job(job_id)

        next_status = job.status
        if job.status == JobStatus.STARTED:
            self._transition(job.status, JobStatus.PROCESSING)
            next_status = JobStatus.PROCESSING
        elif job.status != JobStatus.PROCESSING:
            self._transition(
                job.status, JobStatus.PROCESSING
            )  # Will raise JobStateError

        updated_job = job.model_copy(
            update={
                "status": next_status,
                "progress": progress,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job

    def mark_success(self, job_id: uuid.UUID, result_reference: str) -> JobRecord:
        """Mark the job as SUCCESS."""
        job = self._store.get_job(job_id)
        self._transition(job.status, JobStatus.SUCCESS)

        # Force progress to 100% implicitly upon success
        final_progress = None
        if job.progress:
            final_progress = job.progress.model_copy(
                update={"percentage": 100.0, "current_step": job.progress.total_steps}
            )

        updated_job = job.model_copy(
            update={
                "status": JobStatus.SUCCESS,
                "result_reference": result_reference,
                "progress": final_progress,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job

    def mark_failure(self, job_id: uuid.UUID, error_message: str) -> JobRecord:
        """Mark the job as FAILURE."""
        job = self._store.get_job(job_id)
        self._transition(job.status, JobStatus.FAILURE)

        updated_job = job.model_copy(
            update={
                "status": JobStatus.FAILURE,
                "error_message": error_message,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job

    def mark_retry(self, job_id: uuid.UUID) -> JobRecord:
        """Mark the job for RETRY."""
        job = self._store.get_job(job_id)
        self._transition(job.status, JobStatus.RETRY)

        updated_job = job.model_copy(
            update={
                "status": JobStatus.RETRY,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job

    def cancel_job(self, job_id: uuid.UUID) -> JobRecord:
        """Mark the job as CANCELLED."""
        job = self._store.get_job(job_id)
        self._transition(job.status, JobStatus.CANCELLED)

        updated_job = job.model_copy(
            update={
                "status": JobStatus.CANCELLED,
                "updated_at": datetime.datetime.now(datetime.UTC),
            }
        )
        self._store.update_job(updated_job)
        return updated_job


# Global default instances for loose coupling across the async execution context
_default_store = InMemoryJobStore()
default_task_manager = TaskManager(_default_store)


def get_task_manager() -> TaskManager:
    """Return the global task manager singleton."""
    return default_task_manager
