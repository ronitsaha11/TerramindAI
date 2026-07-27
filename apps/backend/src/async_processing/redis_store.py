from uuid import UUID

import redis

from src.async_processing.exceptions import JobNotFoundError
from src.async_processing.interfaces import JobStoreProtocol
from src.async_processing.models import JobRecord
from src.core.config import settings


class RedisJobStore(JobStoreProtocol):
    """
    Redis implementation of the JobStoreProtocol for distributed execution.
    Uses a synchronous redis client to conform to the existing interface.
    """

    def __init__(self) -> None:
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.prefix = "job:"

    def _key(self, job_id: UUID) -> str:
        return f"{self.prefix}{job_id}"

    def create_job(self, job: JobRecord) -> None:
        self.redis.set(self._key(job.job_id), job.model_dump_json())

    def update_job(self, job: JobRecord) -> None:
        if not self.redis.exists(self._key(job.job_id)):
            raise JobNotFoundError(f"Job {job.job_id} not found in store")
        self.redis.set(self._key(job.job_id), job.model_dump_json())

    def get_job(self, job_id: UUID) -> JobRecord:
        data = self.redis.get(self._key(job_id))
        if not data:
            raise JobNotFoundError(f"Job {job_id} not found in store")
        return JobRecord.model_validate_json(data)

    def delete_job(self, job_id: UUID) -> None:
        self.redis.delete(self._key(job_id))

    def list_jobs(self) -> list[JobRecord]:
        keys = self.redis.keys(f"{self.prefix}*")
        jobs = []
        for k in keys:
            data = self.redis.get(k)
            if data:
                jobs.append(JobRecord.model_validate_json(data))
        return jobs
