from typing import Protocol
from uuid import UUID

from src.async_processing.exceptions import JobNotFoundError
from src.async_processing.models import JobRecord


class JobStoreProtocol(Protocol):
    """
    Protocol for asynchronous job persistence.
    Abstracts the underlying data store (e.g., Redis, PostgreSQL).
    """

    def create_job(self, job: JobRecord) -> None:
        """Persist a new job record."""
        ...

    def update_job(self, job: JobRecord) -> None:
        """Update an existing job record."""
        ...

    def get_job(self, job_id: UUID) -> JobRecord:
        """
        Retrieve a job record by its ID.

        Raises:
            JobNotFoundError: If the job does not exist.
        """
        ...

    def delete_job(self, job_id: UUID) -> None:
        """Remove a job record from the store."""
        ...

    def list_jobs(self) -> list[JobRecord]:
        """Retrieve all job records."""
        ...


class InMemoryJobStore:
    """
    In-memory implementation of the JobStoreProtocol for testing and development.
    """

    def __init__(self) -> None:
        self._store: dict[UUID, JobRecord] = {}

    def create_job(self, job: JobRecord) -> None:
        self._store[job.job_id] = job

    def update_job(self, job: JobRecord) -> None:
        if job.job_id not in self._store:
            raise JobNotFoundError(f"Job {job.job_id} not found in store")
        self._store[job.job_id] = job

    def get_job(self, job_id: UUID) -> JobRecord:
        if job_id not in self._store:
            raise JobNotFoundError(f"Job {job_id} not found in store")
        return self._store[job_id]

    def delete_job(self, job_id: UUID) -> None:
        if job_id in self._store:
            del self._store[job_id]

    def list_jobs(self) -> list[JobRecord]:
        return list(self._store.values())
